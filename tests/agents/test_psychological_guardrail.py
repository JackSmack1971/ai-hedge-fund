"""Tests for the psychological_guardrail_agent (PSY-01)."""

from unittest.mock import patch, MagicMock

from tests.agents.conftest import _make_empty_state
from src.agents.psychological_guardrail import (
    psychological_guardrail_agent,
    _GuardrailReasoning,
)


def _make_state_with_hybrid(tickers=None, analyst_signals=None):
    """Build a state with hybrid_mode enabled."""
    state = _make_empty_state(tickers=tickers or ["AAPL"])
    state["data"]["hybrid_mode"] = True
    if analyst_signals is not None:
        state["data"]["analyst_signals"] = analyst_signals
    return state


def _mock_guardrail_reasoning(*args, **kwargs):
    """Return a _GuardrailReasoning instance regardless of what was passed."""
    return _GuardrailReasoning(reasoning="Mock reasoning from LLM.")


class TestPsychologicalGuardrailAgent:

    def test_no_analyst_signals_returns_neutral_defaults(self):
        """Empty analyst_signals → confidence=50, multiplier=1.0, no flags."""
        state = _make_state_with_hybrid(analyst_signals={})
        result = psychological_guardrail_agent(state)

        output = result["data"]["guardrail_outputs"]["AAPL"]
        assert output["raw_confidence"] == 50
        assert output["confidence_multiplier"] == 1.0
        assert output["calibrated_confidence"] == 50
        assert output["herding_flag"] is False
        assert output["overconfidence_flag"] is False
        assert output["risk_flags"] == []
        assert output["reasoning"] == "No analyst signals available."

    def test_hybrid_mode_off_is_noop(self):
        """When hybrid_mode is False the agent returns empty data."""
        state = _make_empty_state()
        assert "hybrid_mode" not in state["data"] or not state["data"].get("hybrid_mode")
        result = psychological_guardrail_agent(state)
        assert "guardrail_outputs" not in result["data"]

    @patch("src.agents.psychological_guardrail.call_llm", side_effect=_mock_guardrail_reasoning)
    def test_disagreement_reduces_multiplier(self, mock_llm):
        """Mixed bullish/bearish signals → multiplier strictly < 1.0."""
        signals = {
            "analyst_a": {"AAPL": {"signal": "bullish", "confidence": 70}},
            "analyst_b": {"AAPL": {"signal": "bearish", "confidence": 60}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = psychological_guardrail_agent(state)

        output = result["data"]["guardrail_outputs"]["AAPL"]
        assert output["confidence_multiplier"] < 1.0
        assert output["disagreement_score"] > 0.0

    @patch("src.agents.psychological_guardrail.call_llm", side_effect=_mock_guardrail_reasoning)
    def test_unanimous_signals_set_herding_flag(self, mock_llm):
        """All bullish signals (n >= 3) with near-zero disagreement → herding_flag=True."""
        signals = {
            "analyst_a": {"AAPL": {"signal": "bullish", "confidence": 75}},
            "analyst_b": {"AAPL": {"signal": "bullish", "confidence": 80}},
            "analyst_c": {"AAPL": {"signal": "bullish", "confidence": 70}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = psychological_guardrail_agent(state)

        output = result["data"]["guardrail_outputs"]["AAPL"]
        assert output["herding_flag"] is True
        assert "herding_detected" in output["risk_flags"]

    @patch("src.agents.psychological_guardrail.call_llm", side_effect=_mock_guardrail_reasoning)
    def test_overconfidence_flag_triggered(self, mock_llm):
        """High-confidence unanimous signals trigger overconfidence_flag."""
        signals = {
            "analyst_a": {"AAPL": {"signal": "bullish", "confidence": 90}},
            "analyst_b": {"AAPL": {"signal": "bullish", "confidence": 85}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = psychological_guardrail_agent(state)

        output = result["data"]["guardrail_outputs"]["AAPL"]
        assert output["overconfidence_flag"] is True
        assert "overconfidence_warning" in output["risk_flags"]

    @patch("src.agents.psychological_guardrail.call_llm", side_effect=_mock_guardrail_reasoning)
    def test_subjectivity_penalized(self, mock_llm):
        """Majority sentiment analysts → subjectivity_score > 0.3 and high_subjectivity flag."""
        signals = {
            "news_sentiment_analyst": {"AAPL": {"signal": "bullish", "confidence": 70}},
            "sentiment_analyst": {"AAPL": {"signal": "bullish", "confidence": 65}},
            "analyst_c": {"AAPL": {"signal": "neutral", "confidence": 50}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = psychological_guardrail_agent(state)

        output = result["data"]["guardrail_outputs"]["AAPL"]
        # 2 out of 3 are sentiment analysts → subjectivity = 0.6667 > 0.3
        assert output["subjectivity_score"] > 0.3
        assert "high_subjectivity" in output["risk_flags"]

    @patch("src.agents.psychological_guardrail.call_llm", side_effect=_mock_guardrail_reasoning)
    def test_output_stored_in_guardrail_outputs(self, mock_llm):
        """Result contains guardrail_outputs keyed by ticker."""
        signals = {
            "analyst_a": {"AAPL": {"signal": "bullish", "confidence": 70}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = psychological_guardrail_agent(state)

        assert "guardrail_outputs" in result["data"]
        assert "AAPL" in result["data"]["guardrail_outputs"]
        assert result["data"]["guardrail_outputs"]["AAPL"]["ticker"] == "AAPL"

    @patch("src.agents.psychological_guardrail.call_llm", side_effect=_mock_guardrail_reasoning)
    def test_calibrated_confidence_clamped_to_100(self, mock_llm):
        """calibrated_confidence never exceeds 100 even with multiplier near 1."""
        # Use a single analyst with max confidence to approach clamping behavior
        signals = {
            "analyst_a": {"AAPL": {"signal": "bullish", "confidence": 100}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = psychological_guardrail_agent(state)

        output = result["data"]["guardrail_outputs"]["AAPL"]
        assert 0 <= output["calibrated_confidence"] <= 100

    def test_non_analyst_agents_excluded(self):
        """risk_management_agent and portfolio_management_agent do not contribute stances."""
        signals = {
            "risk_management_agent": {"AAPL": {"signal": "bullish", "confidence": 90}},
            "portfolio_management_agent": {"AAPL": {"signal": "bullish", "confidence": 85}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = psychological_guardrail_agent(state)

        # No real analysts → defaults should be used
        output = result["data"]["guardrail_outputs"]["AAPL"]
        assert output["raw_confidence"] == 50
        assert output["reasoning"] == "No analyst signals available."
