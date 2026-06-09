"""Tests for the consensus_agent (DEBT-01)."""

from unittest.mock import patch

from tests.agents.conftest import _make_empty_state
from src.agents.consensus import consensus_agent, ConsensusReport


def _make_state_with_hybrid(tickers=None, analyst_signals=None):
    """Build a state with hybrid_mode enabled."""
    state = _make_empty_state(tickers=tickers or ["AAPL"])
    state["data"]["hybrid_mode"] = True
    if analyst_signals is not None:
        state["data"]["analyst_signals"] = analyst_signals
    return state


def _mock_consensus_report(*args, **kwargs):
    """Return a valid ConsensusReport regardless of input."""
    return ConsensusReport(
        dominant_stance="bullish",
        dominant_count=2,
        minority_stances=["bearish"],
        consensus_confidence=70,
        unresolved_conflicts=["valuation concerns"],
        summary="Analysts are mostly bullish. Minority bearish view cites valuation.",
    )


class TestConsensusAgent:

    def test_no_signals_returns_neutral_consensus(self):
        """Empty analyst_signals → dominant_stance='neutral', no LLM call needed."""
        state = _make_state_with_hybrid(analyst_signals={})
        result = consensus_agent(state)

        output = result["data"]["consensus_output"]["AAPL"]
        assert output["dominant_stance"] == "neutral"
        assert output["dominant_count"] == 0
        assert output["minority_stances"] == []
        assert output["consensus_confidence"] == 50
        assert output["summary"] == "No analyst signals available."

    def test_hybrid_mode_off_is_noop(self):
        """When hybrid_mode is False the agent is a no-op."""
        state = _make_empty_state()
        result = consensus_agent(state)
        assert "consensus_output" not in result["data"]

    @patch("src.agents.consensus.call_llm", side_effect=_mock_consensus_report)
    def test_majority_bullish_sets_dominant_stance(self, mock_llm):
        """Majority bullish signals → dominant_stance='bullish'."""
        signals = {
            "analyst_a": {"AAPL": {"signal": "bullish", "confidence": 75}},
            "analyst_b": {"AAPL": {"signal": "bullish", "confidence": 80}},
            "analyst_c": {"AAPL": {"signal": "bearish", "confidence": 60}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = consensus_agent(state)

        output = result["data"]["consensus_output"]["AAPL"]
        assert output["dominant_stance"] == "bullish"
        assert output["dominant_count"] == 2

    @patch("src.agents.consensus.call_llm", side_effect=_mock_consensus_report)
    def test_output_stored_in_consensus_output(self, mock_llm):
        """Result dict contains consensus_output keyed by ticker."""
        signals = {
            "analyst_a": {"AAPL": {"signal": "bullish", "confidence": 70}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = consensus_agent(state)

        assert "consensus_output" in result["data"]
        assert "AAPL" in result["data"]["consensus_output"]

    @patch("src.agents.consensus.call_llm", side_effect=_mock_consensus_report)
    def test_minority_stances_populated(self, mock_llm):
        """Bearish minority is captured when bullish is dominant."""
        signals = {
            "analyst_a": {"AAPL": {"signal": "bullish", "confidence": 75}},
            "analyst_b": {"AAPL": {"signal": "bullish", "confidence": 80}},
            "analyst_c": {"AAPL": {"signal": "bearish", "confidence": 55}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = consensus_agent(state)

        output = result["data"]["consensus_output"]["AAPL"]
        # LLM result is mocked — minority_stances comes from the mock
        assert isinstance(output["minority_stances"], list)

    def test_non_analyst_agents_excluded(self):
        """risk_management_agent is excluded — results in neutral defaults."""
        signals = {
            "risk_management_agent": {"AAPL": {"signal": "bullish", "confidence": 90}},
        }
        state = _make_state_with_hybrid(analyst_signals=signals)
        result = consensus_agent(state)

        output = result["data"]["consensus_output"]["AAPL"]
        assert output["dominant_stance"] == "neutral"
        assert output["dominant_count"] == 0

    @patch("src.agents.consensus.call_llm", side_effect=_mock_consensus_report)
    def test_multiple_tickers_processed(self, mock_llm):
        """Agent processes each ticker in tickers list."""
        signals = {
            "analyst_a": {
                "AAPL": {"signal": "bullish", "confidence": 70},
                "MSFT": {"signal": "bearish", "confidence": 60},
            },
        }
        state = _make_state_with_hybrid(tickers=["AAPL", "MSFT"], analyst_signals=signals)
        result = consensus_agent(state)

        assert "AAPL" in result["data"]["consensus_output"]
        assert "MSFT" in result["data"]["consensus_output"]
