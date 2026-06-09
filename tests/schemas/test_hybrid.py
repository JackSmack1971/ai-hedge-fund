"""Tests for src/schemas/hybrid.py — Pydantic validation and serialization."""

import pytest
from pydantic import ValidationError

from src.schemas.hybrid import (
    AgentSelection,
    DebateOutput,
    GuardrailOutput,
    HybridDecisionTrace,
    MetaLabelOutput,
    RegimeClassification,
    ThesisOutput,
)


class TestRegimeClassification:
    def test_valid_regime(self):
        rc = RegimeClassification(regime="momentum", confidence=85, reasoning="Strong upward trend")
        assert rc.regime == "momentum"
        assert rc.confidence == 85
        assert rc.reasoning == "Strong upward trend"

    @pytest.mark.parametrize("invalid_regime", ["bull_market", "bear", "", "invalid_regime_label"])
    def test_invalid_regime_literal(self, invalid_regime):
        with pytest.raises(ValidationError):
            RegimeClassification(regime=invalid_regime, confidence=80, reasoning="Test")

    @pytest.mark.parametrize("invalid_confidence", [-1, 101, 150])
    def test_invalid_confidence_bounds(self, invalid_confidence):
        with pytest.raises(ValidationError):
            RegimeClassification(regime="risk_on", confidence=invalid_confidence, reasoning="Test")

    def test_serialization(self):
        rc = RegimeClassification(regime="mean_reversion", confidence=50, reasoning="Bouncing off support")
        dump = rc.model_dump()
        assert dump["regime"] == "mean_reversion"
        assert dump["confidence"] == 50
        assert dump["reasoning"] == "Bouncing off support"
        assert isinstance(rc.model_dump_json(), str)


class TestAgentSelection:
    def test_valid_selection(self):
        sel = AgentSelection(
            ticker="AAPL",
            selected_agents=["warren_buffett", "ben_graham"],
            excluded_agents=["cathie_wood"],
            selection_reasoning={"growth": "growth prospects are moderate, excluding wood"},
        )
        assert sel.ticker == "AAPL"
        assert sel.selected_agents == ["warren_buffett", "ben_graham"]
        assert sel.excluded_agents == ["cathie_wood"]

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AgentSelection(ticker="AAPL", selected_agents=["warren_buffett"])


class TestThesisOutput:
    def test_valid_thesis(self):
        to = ThesisOutput(
            ticker="MSFT",
            stance="bullish",
            confidence=90,
            thesis="Cloud revenue acceleration",
            evidence=["Azure grew 33%"],
            risks=["High valuation multiples"],
        )
        assert to.ticker == "MSFT"
        assert to.stance == "bullish"
        assert to.evidence == ["Azure grew 33%"]

    @pytest.mark.parametrize("invalid_stance", ["long", "short", "flat", ""])
    def test_invalid_stance_literal(self, invalid_stance):
        with pytest.raises(ValidationError):
            ThesisOutput(
                ticker="MSFT",
                stance=invalid_stance,
                confidence=90,
                thesis="Test",
                evidence=[],
                risks=[],
            )

    @pytest.mark.parametrize("invalid_confidence", [-5, 120])
    def test_invalid_confidence_bounds(self, invalid_confidence):
        with pytest.raises(ValidationError):
            ThesisOutput(
                ticker="MSFT",
                stance="neutral",
                confidence=invalid_confidence,
                thesis="Test",
                evidence=[],
                risks=[],
            )


class TestDebateOutput:
    def test_valid_debate(self):
        do = DebateOutput(
            ticker="TSLA",
            bull_case="Robotaxi launch potential",
            bear_case="Declining auto gross margins",
            risk_red_team="Execution risks on autonomous software and regulatory approval",
            unresolved_conflicts=["Timeline of FSD level 4 validation"],
            debate_confidence=75,
        )
        assert do.ticker == "TSLA"
        assert do.debate_confidence == 75

    @pytest.mark.parametrize("invalid_confidence", [-10, 110])
    def test_invalid_confidence_bounds(self, invalid_confidence):
        with pytest.raises(ValidationError):
            DebateOutput(
                ticker="TSLA",
                bull_case="Bull",
                bear_case="Bear",
                risk_red_team="Red",
                unresolved_conflicts=[],
                debate_confidence=invalid_confidence,
            )


class TestGuardrailOutput:
    def test_valid_guardrail(self):
        go = GuardrailOutput(
            ticker="NVDA",
            raw_confidence=95,
            disagreement_score=0.2,
            subjectivity_score=0.4,
            herding_flag=False,
            overconfidence_flag=True,
            calibrated_confidence=80,
            confidence_multiplier=0.85,
            risk_flags=["overconfidence_detected"],
            reasoning="Calibrated due to overconfidence in growth trajectory",
        )
        assert go.ticker == "NVDA"
        assert go.disagreement_score == 0.2
        assert go.confidence_multiplier == 0.85

    @pytest.mark.parametrize(
        "disagreement,subjectivity,multiplier",
        [
            (-0.1, 0.5, 0.8),
            (0.5, 1.2, 0.8),
            (0.5, 0.5, -0.5),
            (1.5, 0.5, 0.8),
            (0.5, 0.5, 1.05),
        ],
    )
    def test_invalid_float_bounds(self, disagreement, subjectivity, multiplier):
        with pytest.raises(ValidationError):
            GuardrailOutput(
                ticker="NVDA",
                raw_confidence=80,
                disagreement_score=disagreement,
                subjectivity_score=subjectivity,
                herding_flag=False,
                overconfidence_flag=False,
                calibrated_confidence=80,
                confidence_multiplier=multiplier,
                risk_flags=[],
                reasoning="Test",
            )


class TestMetaLabelOutput:
    def test_valid_meta_label(self):
        mlo = MetaLabelOutput(
            ticker="AAPL",
            allow_trade=True,
            size_multiplier=0.5,
            label="reduce",
            reasoning="Reduced exposure due to elevated volatility",
        )
        assert mlo.ticker == "AAPL"
        assert mlo.label == "reduce"
        assert mlo.allow_trade is True

    @pytest.mark.parametrize("invalid_label", ["buy", "sell", "hold", ""])
    def test_invalid_label_literal(self, invalid_label):
        with pytest.raises(ValidationError):
            MetaLabelOutput(
                ticker="AAPL",
                allow_trade=True,
                size_multiplier=1.0,
                label=invalid_label,
                reasoning="Test",
            )

    @pytest.mark.parametrize("invalid_multiplier", [-0.01, 1.01])
    def test_invalid_multiplier_bounds(self, invalid_multiplier):
        with pytest.raises(ValidationError):
            MetaLabelOutput(
                ticker="AAPL",
                allow_trade=True,
                size_multiplier=invalid_multiplier,
                label="allow",
                reasoning="Test",
            )


class TestHybridDecisionTrace:
    def test_valid_empty_trace(self):
        hdt = HybridDecisionTrace(ticker="AAPL")
        assert hdt.ticker == "AAPL"
        assert hdt.regime is None
        assert hdt.selected_agents == []
        assert hdt.debate is None
        assert hdt.guardrails is None
        assert hdt.meta_label is None

    def test_valid_full_trace(self):
        rc = RegimeClassification(regime="momentum", confidence=80, reasoning="Upward trend")
        mlo = MetaLabelOutput(ticker="AAPL", allow_trade=True, size_multiplier=1.0, label="allow", reasoning="Clear")
        hdt = HybridDecisionTrace(
            ticker="AAPL",
            regime=rc,
            selected_agents=["analyst_1"],
            meta_label=mlo,
        )
        assert hdt.ticker == "AAPL"
        assert hdt.regime.regime == "momentum"
        assert hdt.meta_label.size_multiplier == 1.0
        assert hdt.debate is None


class TestDecisionD12ExtraFields:
    def test_extra_fields_ignored_on_regime_classification(self):
        result = RegimeClassification.model_validate(
            {"regime": "risk_on", "confidence": 50, "reasoning": "t", "bogus_field": "value"}
        )
        assert result.regime == "risk_on"
        assert not hasattr(result, "bogus_field")

    def test_extra_fields_ignored_on_hybrid_decision_trace(self):
        result = HybridDecisionTrace.model_validate({"ticker": "AAPL", "llm_noise": "value"})
        assert result.ticker == "AAPL"


class TestDecisionD13TraceFields:
    def test_timestamp_field_defaults_none(self):
        from datetime import datetime

        hdt = HybridDecisionTrace(ticker="AAPL")
        assert hdt.timestamp is None

    def test_reasoning_summary_defaults_none(self):
        hdt = HybridDecisionTrace(ticker="AAPL")
        assert hdt.reasoning_summary is None

    def test_full_trace_with_timestamp_and_reasoning(self):
        from datetime import datetime

        hdt = HybridDecisionTrace(
            ticker="AAPL",
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
            reasoning_summary="Bull case is stronger",
        )
        dump = hdt.model_dump()
        assert dump["timestamp"] is not None
        assert dump["reasoning_summary"] == "Bull case is stronger"
