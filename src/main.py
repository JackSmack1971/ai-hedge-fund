import json

from colorama import init
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

import pandas as pd

from src.agents.consensus import consensus_agent
from src.agents.debate import debate_agent
from src.agents.meta_labeler import meta_labeler_agent
from src.agents.portfolio_manager import portfolio_management_agent
from src.agents.psychological_guardrail import psychological_guardrail_agent
from src.agents.risk_manager import risk_management_agent
from src.cli.input import parse_cli_inputs
from src.graph.state import AgentState
from src.regime.classifier import classify_regime
from src.regime.selector import select_analysts_for_regime
from src.schemas.hybrid import RegimeClassification
from src.tools.api import get_prices, prices_to_df
from src.config import src_settings
from src.utils.analysts import get_analyst_nodes
from src.utils.display import print_trading_output
from src.utils.progress import progress

# Load environment variables from .env file
load_dotenv()

init(autoreset=True)


def hybrid_layer_node(state: AgentState) -> dict:
    """Composite node: runs all four hybrid agents sequentially with state threading (D-38)."""
    result = {"messages": [], "data": {}}
    local_state = state
    for agent_fn in [psychological_guardrail_agent, consensus_agent, debate_agent, meta_labeler_agent]:
        partial = agent_fn(local_state)
        result["messages"] = result["messages"] + list(partial.get("messages", []))
        result["data"] = {**result["data"], **partial.get("data", {})}
        local_state = {
            **local_state,
            "data": {**local_state["data"], **partial.get("data", {})},
            "messages": local_state["messages"] + list(partial.get("messages", [])),
        }
    return result


def parse_hedge_fund_response(response):
    """Parses a JSON string and returns a dictionary."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}\nResponse: {repr(response)}")
        return None
    except TypeError as e:
        print(f"Invalid response type (expected string, got {type(response).__name__}): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while parsing response: {e}\nResponse: {repr(response)}")
        return None


##### Run the Hedge Fund #####
def run_hedge_fund(
    tickers: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict,
    show_reasoning: bool = False,
    selected_analysts: list[str] | None = None,
    model_name: str = "gpt-4.1",
    model_provider: str = "OpenAI",
    hybrid_mode: bool = False,
    debate_mode: bool = False,
    adaptive_mode: bool = False,
    reflection_path: str | None = None,
):
    # Start progress tracking
    progress.start()

    try:
        # Adaptive routing: classify regime and filter analysts when enabled (ROUT-01, ROUT-02)
        regime_classification: dict[str, dict] = {}
        regime_selection: dict[str, list] = {}
        effective_analysts = selected_analysts

        if adaptive_mode:
            effective_analysts, regime_classification, regime_selection = _apply_adaptive_routing(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                selected_analysts=selected_analysts,
            )

        # Build workflow (default to all analysts when none provided)
        workflow = create_workflow(effective_analysts if effective_analysts else None)
        agent = workflow.compile()

        final_state = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="Make trading decisions based on the provided data.",
                    )
                ],
                "data": {
                    "tickers": tickers,
                    "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "analyst_signals": {},
                    "hybrid_mode": hybrid_mode,
                    "debate_mode": debate_mode,
                    "regime_classification": regime_classification,
                    "regime_selection": regime_selection,
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    "model_name": model_name,
                    "model_provider": model_provider,
                },
            },
        )

        # Reflection recording: append JSONL trace when path is set (ROUT-03)
        if reflection_path:
            from src.reflection.recorder import record_trace
            record_trace(reflection_path, end_date, final_state)

        return {
            "decisions": parse_hedge_fund_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
        }
    finally:
        # Stop progress tracking
        progress.stop()


def _apply_adaptive_routing(
    tickers: list[str],
    start_date: str,
    end_date: str,
    selected_analysts: list[str] | None,
) -> tuple[list[str] | None, dict[str, dict], dict[str, list]]:
    """Classify regime per ticker, select analysts based on plurality regime.

    Returns (effective_analysts, regime_classification_by_ticker, regime_selection_by_ticker).
    Falls back gracefully on API errors — returns original selected_analysts unchanged.
    """
    api_key = src_settings.financial_datasets_api_key or ""
    analyst_nodes = get_analyst_nodes()
    all_analysts = list(analyst_nodes.keys())
    available = selected_analysts if selected_analysts is not None else all_analysts

    regime_classification: dict[str, dict] = {}
    regime_counts: dict[str, int] = {}

    for ticker in tickers:
        try:
            prices = get_prices(ticker=ticker, start_date=start_date, end_date=end_date, api_key=api_key)
            prices_df = prices_to_df(prices) if prices else pd.DataFrame()
            rc = classify_regime(prices_df)
        except Exception:
            rc = RegimeClassification(regime="unknown", confidence=0, reasoning="API error during regime classification")
        regime_classification[ticker] = rc.model_dump()
        regime_counts[rc.regime] = regime_counts.get(rc.regime, 0) + 1

    # Plurality regime across tickers (most frequent)
    plurality_regime = max(regime_counts, key=lambda r: regime_counts[r]) if regime_counts else "unknown"

    # Select analysts based on plurality regime
    effective = select_analysts_for_regime(plurality_regime, available)

    # Record per-ticker selection
    regime_selection: dict[str, list] = {ticker: effective for ticker in tickers}

    return effective, regime_classification, regime_selection


def start(state: AgentState):
    """Initialize the workflow with the input message."""
    return state


def create_workflow(selected_analysts=None):
    """Create the workflow with selected analysts."""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # Get analyst nodes from the configuration
    analyst_nodes = get_analyst_nodes()

    # Default to all analysts if none selected
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())
    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    # Always add hybrid layer, risk and portfolio management (D-40: hybrid_layer always present)
    workflow.add_node("hybrid_layer", hybrid_layer_node)
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_manager", portfolio_management_agent)

    # Connect selected analysts to hybrid_layer, which then feeds risk_management_agent (D-39)
    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "hybrid_layer")

    workflow.add_edge("hybrid_layer", "risk_management_agent")
    workflow.add_edge("risk_management_agent", "portfolio_manager")
    workflow.add_edge("portfolio_manager", END)

    workflow.set_entry_point("start_node")
    return workflow


if __name__ == "__main__":
    inputs = parse_cli_inputs(
        description="Run the hedge fund trading system",
        require_tickers=True,
        default_months_back=None,
        include_graph_flag=True,
        include_reasoning_flag=True,
    )

    tickers = inputs.tickers
    selected_analysts = inputs.selected_analysts

    # Construct portfolio here
    portfolio = {
        "cash": inputs.initial_cash,
        "margin_requirement": inputs.margin_requirement,
        "margin_used": 0.0,
        "positions": {
            ticker: {
                "long": 0,
                "short": 0,
                "long_cost_basis": 0.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,
                "short": 0.0,
            }
            for ticker in tickers
        },
    }

    result = run_hedge_fund(
        tickers=tickers,
        start_date=inputs.start_date,
        end_date=inputs.end_date,
        portfolio=portfolio,
        show_reasoning=inputs.show_reasoning,
        selected_analysts=inputs.selected_analysts,
        model_name=inputs.model_name,
        model_provider=inputs.model_provider,
    )
    print_trading_output(result)
