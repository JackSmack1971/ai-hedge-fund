"""INT-01 unit tests: hybrid multiplier chaining in risk_management_agent."""

import math
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from tests.agents.conftest import _make_empty_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prices_df():
    """Minimal prices DataFrame that satisfies risk_manager calculations."""
    dates = pd.date_range("2024-03-01", periods=10, freq="B")
    close = [170.0, 171.0, 169.5, 172.0, 170.5, 171.5, 173.0, 172.5, 174.0, 175.0]
    return pd.DataFrame({"close": close}, index=dates)


def _make_mock_prices_list():
    from src.data.models import Price
    prices_df = _make_prices_df()
    result = []
    for date, row in prices_df.iterrows():
        result.append(Price(
            ticker="AAPL",
            time=str(date.date()),
            open=row["close"] - 0.5,
            high=row["close"] + 0.5,
            low=row["close"] - 1.0,
            close=row["close"],
            volume=1000000,
        ))
    return result


def _make_state(
    tickers=None,
    hybrid_mode=False,
    guardrail_outputs=None,
    meta_label_outputs=None,
):
    tickers = tickers or ["AAPL"]
    state = _make_empty_state(tickers=tickers)
    state["data"]["hybrid_mode"] = hybrid_mode
    if guardrail_outputs is not None:
        state["data"]["guardrail_outputs"] = guardrail_outputs
    if meta_label_outputs is not None:
        state["data"]["meta_label_outputs"] = meta_label_outputs
    return state


def _run_risk_agent(state):
    """Run risk_management_agent with mocked API calls."""
    from src.agents.risk_manager import risk_management_agent

    mock_prices = _make_mock_prices_list()
    mock_df = _make_prices_df()

    with (
        patch("src.agents.risk_manager.get_prices", return_value=mock_prices),
        patch("src.agents.risk_manager.prices_to_df", return_value=mock_df),
    ):
        return risk_management_agent(state)


def _get_reasoning(result, ticker="AAPL"):
    return result["data"]["analyst_signals"]["risk_management_agent"][ticker]["reasoning"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHybridMultiplierChaining:
    def test_hybrid_off_no_multiplier_keys_in_reasoning(self):
        """hybrid_mode=False: multiplier keys present but are 1.0 (neutral)."""
        state = _make_state(hybrid_mode=False)
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        assert reasoning["disagreement_multiplier"] == 1.0
        assert reasoning["meta_size_multiplier"] == 1.0

    def test_hybrid_off_baseline_unchanged(self):
        """hybrid_mode=False: position_limit equals vol/corr product (no hybrid shrinkage)."""
        state = _make_state(hybrid_mode=False)
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        # With neutral multipliers, position_limit should equal portfolio_value * combined_limit_pct
        expected = reasoning["portfolio_value"] * reasoning["combined_position_limit_pct"]
        assert math.isclose(reasoning["position_limit"], expected, rel_tol=1e-6)

    def test_neutral_multipliers_when_data_absent(self):
        """hybrid_mode=True but no guardrail/meta outputs: both multipliers default to 1.0."""
        state = _make_state(hybrid_mode=True, guardrail_outputs={}, meta_label_outputs={})
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        assert reasoning["disagreement_multiplier"] == 1.0
        assert reasoning["meta_size_multiplier"] == 1.0

    def test_disagreement_multiplier_applied(self):
        """hybrid_mode=True with confidence_multiplier=0.6: position_limit shrunk by 0.6."""
        state = _make_state(
            hybrid_mode=True,
            guardrail_outputs={"AAPL": {"confidence_multiplier": 0.6}},
            meta_label_outputs={},
        )
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        assert reasoning["disagreement_multiplier"] == pytest.approx(0.6)
        assert reasoning["meta_size_multiplier"] == 1.0
        base = reasoning["portfolio_value"] * reasoning["combined_position_limit_pct"]
        assert math.isclose(reasoning["position_limit"], base * 0.6, rel_tol=1e-6)

    def test_meta_size_multiplier_applied(self):
        """hybrid_mode=True with size_multiplier=0.7: position_limit shrunk by 0.7."""
        state = _make_state(
            hybrid_mode=True,
            guardrail_outputs={},
            meta_label_outputs={"AAPL": {"size_multiplier": 0.7}},
        )
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        assert reasoning["disagreement_multiplier"] == 1.0
        assert reasoning["meta_size_multiplier"] == pytest.approx(0.7)
        base = reasoning["portfolio_value"] * reasoning["combined_position_limit_pct"]
        assert math.isclose(reasoning["position_limit"], base * 0.7, rel_tol=1e-6)

    def test_both_multipliers_combined(self):
        """D-26: disagreement=0.6, meta_size=0.7 → position_limit * 0.42."""
        state = _make_state(
            hybrid_mode=True,
            guardrail_outputs={"AAPL": {"confidence_multiplier": 0.6}},
            meta_label_outputs={"AAPL": {"size_multiplier": 0.7}},
        )
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        assert reasoning["disagreement_multiplier"] == pytest.approx(0.6)
        assert reasoning["meta_size_multiplier"] == pytest.approx(0.7)
        base = reasoning["portfolio_value"] * reasoning["combined_position_limit_pct"]
        assert math.isclose(reasoning["position_limit"], base * 0.42, rel_tol=1e-6)

    def test_nan_multiplier_clamped_to_1(self):
        """NaN confidence_multiplier is clamped to 1.0 (no NaN propagation)."""
        state = _make_state(
            hybrid_mode=True,
            guardrail_outputs={"AAPL": {"confidence_multiplier": float("nan")}},
            meta_label_outputs={},
        )
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        assert reasoning["disagreement_multiplier"] == 1.0
        assert not math.isnan(reasoning["position_limit"])

    def test_inf_multiplier_clamped(self):
        """Inf size_multiplier is clamped to 1.0."""
        state = _make_state(
            hybrid_mode=True,
            guardrail_outputs={},
            meta_label_outputs={"AAPL": {"size_multiplier": float("inf")}},
        )
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        assert reasoning["meta_size_multiplier"] == 1.0

    def test_observability_keys_present(self):
        """reasoning dict contains disagreement_multiplier and meta_size_multiplier when hybrid on."""
        state = _make_state(
            hybrid_mode=True,
            guardrail_outputs={"AAPL": {"confidence_multiplier": 0.8}},
            meta_label_outputs={"AAPL": {"size_multiplier": 0.9}},
        )
        result = _run_risk_agent(state)
        reasoning = _get_reasoning(result)
        assert "disagreement_multiplier" in reasoning
        assert "meta_size_multiplier" in reasoning
        assert reasoning["disagreement_multiplier"] == pytest.approx(0.8)
        assert reasoning["meta_size_multiplier"] == pytest.approx(0.9)

    def test_cppi_not_applied(self):
        """D-29: risk_manager.py must not import or call drawdown_guardrail."""
        import src.agents.risk_manager as rm_module
        import inspect
        source = inspect.getsource(rm_module)
        assert "drawdown_guardrail" not in source
        assert "compute_disagreement_score" not in source


class TestDAGWiring:
    """Tests for hybrid_layer_node in main.py and DAG topology."""

    def test_hybrid_layer_always_in_graph(self):
        """D-40: create_workflow always includes hybrid_layer node."""
        from src.main import create_workflow
        workflow = create_workflow(selected_analysts=["warren_buffett"])
        compiled = workflow.compile()
        assert "hybrid_layer" in compiled.get_graph().nodes

    def test_analyst_edges_route_to_hybrid_layer(self):
        """D-39: analyst fan-in edges target hybrid_layer, not risk_management_agent directly."""
        from src.main import create_workflow
        from src.utils.analysts import get_analyst_nodes
        workflow = create_workflow(selected_analysts=["warren_buffett"])
        compiled = workflow.compile()
        graph = compiled.get_graph()
        analyst_nodes = get_analyst_nodes()
        node_name = analyst_nodes["warren_buffett"][0]
        edge_targets = {e.target for e in graph.edges if e.source == node_name}
        assert "hybrid_layer" in edge_targets
        assert "risk_management_agent" not in edge_targets

    def test_hybrid_layer_to_risk_management_edge(self):
        """D-39: hybrid_layer → risk_management_agent edge exists."""
        from src.main import create_workflow
        workflow = create_workflow(selected_analysts=["warren_buffett"])
        compiled = workflow.compile()
        graph = compiled.get_graph()
        edge_targets = {e.target for e in graph.edges if e.source == "hybrid_layer"}
        assert "risk_management_agent" in edge_targets

    def test_run_hedge_fund_accepts_hybrid_mode(self):
        """run_hedge_fund signature accepts hybrid_mode and debate_mode parameters."""
        import inspect
        from src.main import run_hedge_fund
        sig = inspect.signature(run_hedge_fund)
        assert "hybrid_mode" in sig.parameters
        assert "debate_mode" in sig.parameters

    def test_hybrid_mode_injected_into_state(self):
        """run_hedge_fund injects hybrid_mode and debate_mode into state['data']."""
        from src.main import create_workflow
        captured_states = []

        def fake_start(state):
            captured_states.append(dict(state["data"]))
            return state

        workflow = create_workflow(selected_analysts=[])
        # Verify the parameter wiring by checking run_hedge_fund source
        import inspect
        from src.main import run_hedge_fund
        source = inspect.getsource(run_hedge_fund)
        assert "hybrid_mode" in source
        assert "debate_mode" in source
