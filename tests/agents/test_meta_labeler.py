"""Tests for meta_labeler_agent (META-01)."""

from unittest.mock import MagicMock, patch

from tests.agents.conftest import _make_empty_state


def _make_state(
    tickers=None,
    hybrid_mode=True,
    guardrail_outputs=None,
    debate_outputs=None,
):
    """Build a minimal state for meta_labeler_agent tests."""
    state = _make_empty_state(tickers=tickers or ["AAPL"])
    state["data"]["hybrid_mode"] = hybrid_mode
    state["data"]["guardrail_outputs"] = guardrail_outputs or {}
    state["data"]["debate_outputs"] = debate_outputs or {}
    return state


def _make_guardrail(calibrated_confidence=70, confidence_multiplier=0.8):
    return {
        "calibrated_confidence": calibrated_confidence,
        "confidence_multiplier": confidence_multiplier,
    }


def _make_debate(n_conflicts=0):
    return {
        "unresolved_conflicts": [f"conflict_{i}" for i in range(n_conflicts)],
    }


def _fake_llm(prompt, pydantic_model, agent_name=None, state=None, **kwargs):
    m = MagicMock()
    m.reasoning = "Meta-label assigned based on calibrated confidence and multiplier thresholds."
    return m


class TestMetaLabelerHybridModeOff:
    def test_hybrid_mode_off_is_noop(self):
        """When hybrid_mode=False, agent returns empty data and unmodified messages."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(hybrid_mode=False)
        result = meta_labeler_agent(state)

        assert result["data"] == {}
        assert result["messages"] == state["messages"]

    def test_hybrid_mode_off_does_not_call_llm(self):
        """When hybrid_mode=False, no LLM calls are made."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(hybrid_mode=False)
        with patch("src.agents.meta_labeler.call_llm") as mock_llm:
            meta_labeler_agent(state)
            mock_llm.assert_not_called()


class TestMetaLabelerSuppressLabel:
    def test_suppress_label_when_confidence_below_threshold(self):
        """calibrated_confidence < 30 => suppress, allow_trade=False, size_multiplier=0.0."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=25, confidence_multiplier=0.9)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        output = result["data"]["meta_label_outputs"]["AAPL"]
        assert output["label"] == "suppress"
        assert output["allow_trade"] is False
        assert output["size_multiplier"] == 0.0

    def test_suppress_label_when_multiplier_below_threshold(self):
        """confidence_multiplier < 0.40 => suppress, allow_trade=False, size_multiplier=0.0."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=60, confidence_multiplier=0.35)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        output = result["data"]["meta_label_outputs"]["AAPL"]
        assert output["label"] == "suppress"
        assert output["allow_trade"] is False
        assert output["size_multiplier"] == 0.0

    def test_suppress_label_at_boundary_confidence_29(self):
        """calibrated_confidence=29 is below threshold 30 => suppress."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=29, confidence_multiplier=0.9)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        assert result["data"]["meta_label_outputs"]["AAPL"]["label"] == "suppress"


class TestMetaLabelerHoldOnlyLabel:
    def test_hold_only_label_when_medium_confidence(self):
        """calibrated_confidence in [30,49] with good multiplier => hold_only."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=40, confidence_multiplier=0.9)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        output = result["data"]["meta_label_outputs"]["AAPL"]
        assert output["label"] == "hold_only"
        assert output["allow_trade"] is True
        assert output["size_multiplier"] == 0.5

    def test_hold_only_label_when_multiplier_medium(self):
        """confidence_multiplier in [0.40, 0.59] => hold_only."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=70, confidence_multiplier=0.55)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        output = result["data"]["meta_label_outputs"]["AAPL"]
        assert output["label"] == "hold_only"
        assert output["allow_trade"] is True
        assert output["size_multiplier"] == 0.5

    def test_hold_only_boundary_confidence_30(self):
        """calibrated_confidence=30 is NOT below 30, check lower band of hold_only."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=30, confidence_multiplier=0.9)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        # 30 is not < 30 (suppress) but 30 < 50 => hold_only
        assert result["data"]["meta_label_outputs"]["AAPL"]["label"] == "hold_only"


class TestMetaLabelerReduceLabel:
    def test_reduce_label_when_three_or_more_conflicts(self):
        """n_conflicts >= 3 with passing confidence/multiplier => reduce."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=70, confidence_multiplier=0.8)},
            debate_outputs={"AAPL": _make_debate(n_conflicts=3)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        output = result["data"]["meta_label_outputs"]["AAPL"]
        assert output["label"] == "reduce"
        assert output["allow_trade"] is True
        assert output["size_multiplier"] == 0.7

    def test_reduce_label_with_five_conflicts(self):
        """n_conflicts=5 with passing confidence => reduce."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=75, confidence_multiplier=0.85)},
            debate_outputs={"AAPL": _make_debate(n_conflicts=5)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        assert result["data"]["meta_label_outputs"]["AAPL"]["label"] == "reduce"

    def test_reduce_not_triggered_with_two_conflicts(self):
        """n_conflicts=2 is below threshold, should not trigger reduce by itself."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=70, confidence_multiplier=0.8)},
            debate_outputs={"AAPL": _make_debate(n_conflicts=2)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        # 2 conflicts is not >= 3, should be allow
        assert result["data"]["meta_label_outputs"]["AAPL"]["label"] == "allow"


class TestMetaLabelerAllowLabel:
    def test_allow_label_when_all_conditions_good(self):
        """Good confidence + high multiplier + no conflicts => allow."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=80, confidence_multiplier=0.9)},
            debate_outputs={"AAPL": _make_debate(n_conflicts=0)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        output = result["data"]["meta_label_outputs"]["AAPL"]
        assert output["label"] == "allow"
        assert output["allow_trade"] is True
        assert output["size_multiplier"] == round(0.9, 4)

    def test_allow_size_multiplier_is_confidence_multiplier(self):
        """allow label: size_multiplier = confidence_multiplier (rounded to 4 decimals)."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=90, confidence_multiplier=0.9876)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        output = result["data"]["meta_label_outputs"]["AAPL"]
        assert output["label"] == "allow"
        assert output["size_multiplier"] == round(0.9876, 4)


class TestMetaLabelerPriority:
    def test_suppress_takes_priority_over_reduce(self):
        """Low confidence + many conflicts: suppress wins over reduce."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=20, confidence_multiplier=0.9)},
            debate_outputs={"AAPL": _make_debate(n_conflicts=5)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        assert result["data"]["meta_label_outputs"]["AAPL"]["label"] == "suppress"

    def test_suppress_takes_priority_over_hold_only(self):
        """Very low multiplier (< 0.40) wins over medium confidence."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=45, confidence_multiplier=0.30)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        assert result["data"]["meta_label_outputs"]["AAPL"]["label"] == "suppress"

    def test_hold_only_takes_priority_over_reduce(self):
        """Medium confidence + many conflicts: hold_only wins over reduce."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=45, confidence_multiplier=0.9)},
            debate_outputs={"AAPL": _make_debate(n_conflicts=5)},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        assert result["data"]["meta_label_outputs"]["AAPL"]["label"] == "hold_only"


class TestMetaLabelerOutputStorage:
    def test_output_stored_in_meta_label_outputs(self):
        """result['data']['meta_label_outputs'] is populated correctly."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail()},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        assert "meta_label_outputs" in result["data"]
        assert "AAPL" in result["data"]["meta_label_outputs"]
        output = result["data"]["meta_label_outputs"]["AAPL"]
        assert output["ticker"] == "AAPL"
        assert "allow_trade" in output
        assert "size_multiplier" in output
        assert "label" in output
        assert "reasoning" in output

    def test_message_added_to_state(self):
        """A HumanMessage is appended to messages after meta-labeling."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail()},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        assert len(result["messages"]) == 1
        assert result["messages"][0].name == "meta_labeler_agent"

    def test_no_guardrail_output_uses_defaults(self):
        """When guardrail_outputs is empty, defaults (confidence=50, mult=1.0) are used."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state()  # no guardrail_outputs
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        output = result["data"]["meta_label_outputs"]["AAPL"]
        # With defaults: confidence=50 (not < 30, not < 50), multiplier=1.0 (not < 0.40, not < 0.60)
        # n_conflicts=0 (no debate output), label should be "allow"
        assert output["label"] == "allow"

    def test_none_debate_output_treated_as_zero_conflicts(self):
        """When debate_outputs[ticker] is None, n_conflicts=0."""
        from src.agents.meta_labeler import meta_labeler_agent

        state = _make_state(
            guardrail_outputs={"AAPL": _make_guardrail(calibrated_confidence=70, confidence_multiplier=0.8)},
            debate_outputs={"AAPL": None},
        )
        with patch("src.agents.meta_labeler.call_llm", side_effect=_fake_llm):
            result = meta_labeler_agent(state)

        # n_conflicts=0 with good confidence => allow
        assert result["data"]["meta_label_outputs"]["AAPL"]["label"] == "allow"
