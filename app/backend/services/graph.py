import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
import json
import re
from collections import deque

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from app.backend.services.agent_service import create_agent_function
from src.agents.portfolio_manager import portfolio_management_agent
from src.agents.risk_manager import risk_management_agent
from src.graph.state import AgentState, start
from src.utils.analysts import ANALYST_CONFIG

logger = logging.getLogger(__name__)

GRAPH_EXECUTOR = ThreadPoolExecutor(max_workers=32, thread_name_prefix="graph")


def sanitize_request_payload(request):
    """Return a request object or dict with plaintext API keys removed."""
    if request is None:
        return None

    if hasattr(request, "model_copy"):
        return request.model_copy(update={"api_keys": None})

    if isinstance(request, dict):
        sanitized = {}
        for key, value in request.items():
            if key == "api_keys":
                continue
            sanitized[key] = sanitize_request_payload(value)
        return sanitized

    if isinstance(request, list):
        return [sanitize_request_payload(value) for value in request]

    return request


def extract_base_agent_key(unique_id: str) -> str:
    """
    Extract the base agent key from a unique node ID.

    Args:
        unique_id: The unique node ID with suffix (e.g., "warren_buffett_abc123")

    Returns:
        The base agent key (e.g., "warren_buffett")
    """
    # For agent nodes, remove the last underscore and 6-character suffix
    parts = unique_id.split("_")
    if len(parts) >= 2:
        last_part = parts[-1]
        # If the last part is a 6-character alphanumeric string, it's likely our suffix
        if len(last_part) == 6 and re.match(r"^[a-z0-9]+$", last_part):
            return "_".join(parts[:-1])
    return unique_id  # Return original if no suffix pattern found


def _add_planned_edge(
    planned_edges: list[tuple[str, str]],
    planned_edge_set: set[tuple[str, str]],
    source: str,
    target: str,
) -> None:
    """Record a unique planned edge while rejecting self-loops early."""
    if source == target:
        raise ValueError(f"Self-loop edges are not allowed: {source}")

    edge = (source, target)
    if edge in planned_edge_set:
        return

    planned_edge_set.add(edge)
    planned_edges.append(edge)


def _validate_planned_edges_are_acyclic(planned_edges: list[tuple[str, str]]) -> None:
    """Reject graph edge sets that contain a directed cycle."""
    adjacency: dict[str, set[str]] = {}
    in_degree: dict[str, int] = {}
    nodes: set[str] = set()

    for source, target in planned_edges:
        nodes.add(source)
        nodes.add(target)
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set())
        in_degree[target] = in_degree.get(target, 0) + 1
        in_degree.setdefault(source, in_degree.get(source, 0))

    queue = deque(sorted(node for node in nodes if in_degree.get(node, 0) == 0))
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for target in sorted(adjacency.get(node, set())):
            in_degree[target] -= 1
            if in_degree[target] == 0:
                queue.append(target)

    if visited != len(nodes):
        raise ValueError("Cyclic graph configurations are not allowed")


# Helper function to create the agent graph
def create_graph(graph_nodes: list, graph_edges: list) -> StateGraph:
    """Create the workflow based on the React Flow graph structure."""
    graph = StateGraph(AgentState)
    graph.add_node("start_node", start)

    # Get analyst nodes from the configuration
    analyst_nodes = {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}

    # Extract agent IDs from graph structure
    agent_ids = [node.id for node in graph_nodes]
    agent_ids_set = set(agent_ids)

    # Track which nodes are portfolio managers for special handling
    portfolio_manager_nodes = set()

    # Add agent nodes
    for unique_agent_id in agent_ids:
        base_agent_key = extract_base_agent_key(unique_agent_id)

        # Track portfolio manager nodes for special handling (before ANALYST_CONFIG check)
        if base_agent_key == "portfolio_manager":
            portfolio_manager_nodes.add(unique_agent_id)
            continue

        # Skip if the base agent key is not in our analyst configuration
        if base_agent_key not in ANALYST_CONFIG:
            continue

        node_name, node_func = analyst_nodes[base_agent_key]
        agent_function = create_agent_function(node_func, unique_agent_id)  # type: ignore[arg-type]
        graph.add_node(unique_agent_id, agent_function)

    # Add portfolio manager nodes and their corresponding risk managers
    risk_manager_nodes = {}  # Map portfolio manager ID to risk manager ID
    for portfolio_manager_id in portfolio_manager_nodes:
        portfolio_manager_function = create_agent_function(portfolio_management_agent, portfolio_manager_id)
        graph.add_node(portfolio_manager_id, portfolio_manager_function)

        # Create unique risk manager for this portfolio manager
        suffix = portfolio_manager_id.split("_")[-1]
        risk_manager_id = f"risk_management_agent_{suffix}"
        risk_manager_nodes[portfolio_manager_id] = risk_manager_id

        # Add the risk manager node
        risk_manager_function = create_agent_function(risk_management_agent, risk_manager_id)
        graph.add_node(risk_manager_id, risk_manager_function)

    # Build connections based on React Flow graph structure
    nodes_with_incoming_edges = set()
    nodes_with_outgoing_edges = set()
    direct_to_portfolio_managers = {}  # Map analyst ID to portfolio manager ID for direct connections
    planned_edges: list[tuple[str, str]] = []
    planned_edge_set: set[tuple[str, str]] = set()

    for edge in graph_edges:
        # Only consider edges between agent nodes (not from stock tickers)
        if edge.source in agent_ids_set and edge.target in agent_ids_set:
            source_base_key = extract_base_agent_key(edge.source)
            target_base_key = extract_base_agent_key(edge.target)

            nodes_with_incoming_edges.add(edge.target)
            nodes_with_outgoing_edges.add(edge.source)

            # Check if this is a direct connection from analyst to portfolio manager
            if (
                source_base_key in ANALYST_CONFIG
                and source_base_key != "portfolio_manager"
                and target_base_key == "portfolio_manager"
            ):
                # Don't add direct edge to portfolio manager - we'll route through risk manager
                direct_to_portfolio_managers[edge.source] = edge.target
            else:
                # Add edge between agent nodes (but not direct to portfolio managers)
                _add_planned_edge(planned_edges, planned_edge_set, edge.source, edge.target)

    # Connect start_node to nodes that don't have incoming edges from other agents
    for agent_id in agent_ids:
        if agent_id not in nodes_with_incoming_edges:
            base_agent_key = extract_base_agent_key(agent_id)
            if base_agent_key in ANALYST_CONFIG and base_agent_key != "portfolio_manager":
                _add_planned_edge(planned_edges, planned_edge_set, "start_node", agent_id)

    # Connect analysts that have direct connections to portfolio managers to their corresponding risk managers
    for analyst_id, portfolio_manager_id in direct_to_portfolio_managers.items():
        risk_manager_id = risk_manager_nodes[portfolio_manager_id]
        _add_planned_edge(planned_edges, planned_edge_set, analyst_id, risk_manager_id)

    # Connect each risk manager to its corresponding portfolio manager
    for portfolio_manager_id, risk_manager_id in risk_manager_nodes.items():
        _add_planned_edge(planned_edges, planned_edge_set, risk_manager_id, portfolio_manager_id)

    # Connect portfolio managers to END
    for portfolio_manager_id in portfolio_manager_nodes:
        _add_planned_edge(planned_edges, planned_edge_set, portfolio_manager_id, END)

    _validate_planned_edges_are_acyclic(planned_edges)

    for source, target in planned_edges:
        graph.add_edge(source, target)

    # If the graph has no portfolio manager, make sure terminal analyst nodes can finish.
    if not portfolio_manager_nodes:
        for agent_id in agent_ids:
            base_agent_key = extract_base_agent_key(agent_id)
            if base_agent_key in ANALYST_CONFIG and agent_id not in nodes_with_outgoing_edges:
                graph.add_edge(agent_id, END)

    # Set the entry point to the start node
    graph.set_entry_point("start_node")
    return graph


async def run_graph_async(graph, portfolio, tickers, start_date, end_date, model_name, model_provider, request=None):
    """Async wrapper for run_graph to work with asyncio."""
    loop = asyncio.get_running_loop()
    context = copy_context()
    return await loop.run_in_executor(
        GRAPH_EXECUTOR,
        lambda: context.run(run_graph, graph, portfolio, tickers, start_date, end_date, model_name, model_provider, request),
    )


def run_graph(
    graph: StateGraph,
    portfolio: dict,
    tickers: list[str],
    start_date: str,
    end_date: str,
    model_name: str,
    model_provider: str,
    request=None,
) -> dict:
    """
    Run the graph with the given portfolio, tickers,
    start date, end date, show reasoning, model name,
    and model provider.
    """
    return graph.invoke(  # type: ignore[attr-defined]
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
            },
            "metadata": {
                "show_reasoning": False,
                "model_name": model_name,
                "model_provider": model_provider,
                "request": sanitize_request_payload(request),  # Keep secrets out of AgentState
            },
        },
        config={"recursion_limit": 50},
    )


def parse_hedge_fund_response(response):
    """Parses a JSON string and returns a dictionary."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.exception("JSON decoding error while parsing LLM response: %r", response)
        return None
    except TypeError as e:
        logger.exception("Invalid response type while parsing LLM response: %s", type(response).__name__)
        return None
    except Exception as e:
        logger.exception("Unexpected error while parsing LLM response: %r", response)
        return None
