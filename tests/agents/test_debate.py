"""Tests for debate_agent (DEBT-02)."""

from unittest.mock import MagicMock, call, patch

from tests.agents.conftest import _make_empty_state


def _make_state(tickers=None, hybrid_mode=True, debate_mode=True, analyst_signals=None):
    """Build a minimal state for debate agent tests."""
    state = _make_empty_state(tickers=tickers or ["AAPL"])
    state["data"]["hybrid_mode"] = hybrid_mode
    state["data"]["debate_mode"] = debate_mode
    if analyst_signals is not None:
        state["data"]["analyst_signals"] = analyst_signals
    return state


def _make_bull_case():
    m = MagicMock()
    m.bull_case = "Strong revenue growth and market dominance."
    return m


def _make_bear_case():
    m = MagicMock()
    m.bear_case = "Valuation too stretched, macro headwinds."
    return m


def _make_red_team(conflicts=None):
    m = MagicMock()
    m.risk_red_team = "Both cases ignore regulatory risk."
    m.unresolved_conflicts = conflicts if conflicts is not None else ["Valuation gap", "Macro sensitivity"]
    m.debate_confidence = 65
    return m


class TestDebateAgentHybridModeOff:
    def test_hybrid_mode_off_is_noop(self):
        """When hybrid_mode=False, agent returns empty data and unmodified messages."""
        from src.agents.debate import debate_agent

        state = _make_state(hybrid_mode=False)
        result = debate_agent(state)

        assert result["data"] == {}
        assert result["messages"] == state["messages"]

    def test_hybrid_mode_off_does_not_call_llm(self):
        """When hybrid_mode=False, no LLM calls should be made."""
        from src.agents.debate import debate_agent

        state = _make_state(hybrid_mode=False)
        with patch("src.agents.debate.call_llm") as mock_llm:
            debate_agent(state)
            mock_llm.assert_not_called()


class TestDebateModeFalse:
    def test_debate_mode_off_stores_none_per_ticker(self):
        """When debate_mode=False, debate_outputs[ticker] must be None."""
        from src.agents.debate import debate_agent

        state = _make_state(debate_mode=False)
        with patch("src.agents.debate.call_llm") as mock_llm:
            result = debate_agent(state)

        assert "debate_outputs" in result["data"]
        assert result["data"]["debate_outputs"]["AAPL"] is None
        mock_llm.assert_not_called()

    def test_debate_mode_off_stores_none_for_all_tickers(self):
        """All tickers get None when debate_mode=False."""
        from src.agents.debate import debate_agent

        state = _make_state(tickers=["AAPL", "MSFT"], debate_mode=False)
        with patch("src.agents.debate.call_llm") as mock_llm:
            result = debate_agent(state)

        assert result["data"]["debate_outputs"]["AAPL"] is None
        assert result["data"]["debate_outputs"]["MSFT"] is None
        mock_llm.assert_not_called()


class TestDebateModeTrue:
    def test_debate_mode_on_calls_llm_three_times_per_ticker(self):
        """Exactly 3 call_llm calls per ticker when debate_mode=True."""
        from src.agents.debate import debate_agent

        state = _make_state()
        call_count = [0]

        def fake_llm(prompt, pydantic_model, agent_name=None, state=None, **kwargs):
            call_count[0] += 1
            count = call_count[0]
            if count % 3 == 1:
                return _make_bull_case()
            elif count % 3 == 2:
                return _make_bear_case()
            else:
                return _make_red_team()

        with patch("src.agents.debate.call_llm", side_effect=fake_llm):
            debate_agent(state)

        assert call_count[0] == 3

    def test_debate_mode_on_calls_llm_three_times_per_ticker_multi(self):
        """3 call_llm calls per ticker: 2 tickers = 6 total calls."""
        from src.agents.debate import debate_agent

        state = _make_state(tickers=["AAPL", "MSFT"])
        call_count = [0]

        def fake_llm(prompt, pydantic_model, agent_name=None, state=None, **kwargs):
            call_count[0] += 1
            count = call_count[0]
            if count % 3 == 1:
                return _make_bull_case()
            elif count % 3 == 2:
                return _make_bear_case()
            else:
                return _make_red_team()

        with patch("src.agents.debate.call_llm", side_effect=fake_llm):
            debate_agent(state)

        assert call_count[0] == 6

    def test_debate_output_stored_in_debate_outputs(self):
        """After debate_mode=True, debate_outputs[ticker] is a non-None dict."""
        from src.agents.debate import debate_agent

        state = _make_state()
        call_count = [0]

        def fake_llm(prompt, pydantic_model, agent_name=None, state=None, **kwargs):
            call_count[0] += 1
            count = call_count[0]
            if count % 3 == 1:
                return _make_bull_case()
            elif count % 3 == 2:
                return _make_bear_case()
            else:
                return _make_red_team()

        with patch("src.agents.debate.call_llm", side_effect=fake_llm):
            result = debate_agent(state)

        assert "debate_outputs" in result["data"]
        assert result["data"]["debate_outputs"]["AAPL"] is not None
        assert isinstance(result["data"]["debate_outputs"]["AAPL"], dict)

    def test_debate_output_has_correct_fields(self):
        """DebateOutput dict has all expected fields with correct types."""
        from src.agents.debate import debate_agent

        state = _make_state()
        call_count = [0]

        def fake_llm(prompt, pydantic_model, agent_name=None, state=None, **kwargs):
            call_count[0] += 1
            count = call_count[0]
            if count % 3 == 1:
                return _make_bull_case()
            elif count % 3 == 2:
                return _make_bear_case()
            else:
                return _make_red_team(conflicts=["conflict A", "conflict B"])

        with patch("src.agents.debate.call_llm", side_effect=fake_llm):
            result = debate_agent(state)

        output = result["data"]["debate_outputs"]["AAPL"]
        assert output["ticker"] == "AAPL"
        assert isinstance(output["bull_case"], str)
        assert isinstance(output["bear_case"], str)
        assert isinstance(output["risk_red_team"], str)
        assert isinstance(output["unresolved_conflicts"], list)
        assert isinstance(output["debate_confidence"], int)
        assert 0 <= output["debate_confidence"] <= 100

    def test_analyst_signals_included_in_context(self):
        """Analyst signals for the ticker are included in the bull/bear prompts."""
        from src.agents.debate import debate_agent

        signals = {
            "warren_buffett_agent": {"AAPL": {"signal": "bullish", "confidence": 80, "reasoning": "strong moat"}},
        }
        state = _make_state(analyst_signals=signals)
        call_count = [0]
        captured_prompts = []

        def fake_llm(prompt, pydantic_model, agent_name=None, state=None, **kwargs):
            call_count[0] += 1
            captured_prompts.append(prompt)
            count = call_count[0]
            if count % 3 == 1:
                return _make_bull_case()
            elif count % 3 == 2:
                return _make_bear_case()
            else:
                return _make_red_team()

        with patch("src.agents.debate.call_llm", side_effect=fake_llm):
            debate_agent(state)

        # At least one prompt should mention warren_buffett_agent
        all_content = " ".join(str(p) for p in captured_prompts)
        assert "warren_buffett_agent" in all_content

    def test_message_added_to_state(self):
        """A HumanMessage is appended to messages after debate."""
        from src.agents.debate import debate_agent

        state = _make_state()
        call_count = [0]

        def fake_llm(prompt, pydantic_model, agent_name=None, state=None, **kwargs):
            call_count[0] += 1
            count = call_count[0]
            if count % 3 == 1:
                return _make_bull_case()
            elif count % 3 == 2:
                return _make_bear_case()
            else:
                return _make_red_team()

        with patch("src.agents.debate.call_llm", side_effect=fake_llm):
            result = debate_agent(state)

        assert len(result["messages"]) == 1
        assert result["messages"][0].name == "debate_agent"
