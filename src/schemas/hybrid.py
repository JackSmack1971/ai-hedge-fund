"""Pydantic schemas for the hybrid decision engine components.

These schemas establish the structured interface and boundary rules for data passing
between Graph-of-Agents, Safe Debate, Psychological Guardrails, Meta-Labeler,
and Risk/Portfolio management layers.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RegimeClassification(BaseModel):
    """Represents the market regime classification for a given context."""

    model_config = ConfigDict(extra="ignore")

    regime: Literal[
        "risk_on",
        "risk_off",
        "high_volatility",
        "low_volatility",
        "momentum",
        "mean_reversion",
        "news_shock",
        "valuation_stress",
        "unknown",
    ] = Field(description="The identified market regime label")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score in the range [0, 100]")
    reasoning: str = Field(..., description="Explanation/justification for the classification")


class AgentSelection(BaseModel):
    """Records the selection of agents for analysis of a specific ticker."""

    model_config = ConfigDict(extra="ignore")

    ticker: str = Field(..., description="The stock ticker symbol")
    selected_agents: List[str] = Field(..., description="List of agent IDs selected for execution")
    excluded_agents: List[str] = Field(..., description="List of agent IDs excluded from execution")
    selection_reasoning: Dict[str, str] = Field(
        ..., description="Reasoning mapping for the selected/excluded agent categories"
    )


class ThesisOutput(BaseModel):
    """Represents a generated bullish, bearish, or neutral thesis for a ticker."""

    model_config = ConfigDict(extra="ignore")

    ticker: str = Field(..., description="The stock ticker symbol")
    stance: Literal["bullish", "bearish", "neutral"] = Field(..., description="The core stance or outlook")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score in the range [0, 100]")
    thesis: str = Field(..., description="Detailed thesis text outlining the argument")
    evidence: List[str] = Field(..., description="Supporting evidence bullet points")
    risks: List[str] = Field(..., description="Identified counterarguments or risk factors")


class DebateOutput(BaseModel):
    """Represents the structured output of a Safe Debate round for a ticker."""

    model_config = ConfigDict(extra="ignore")

    ticker: str = Field(..., description="The stock ticker symbol")
    bull_case: str = Field(..., description="The strongest bull argument/case")
    bear_case: str = Field(..., description="The strongest bear argument/case")
    risk_red_team: str = Field(..., description="The critical attack on both cases by the risk red team")
    unresolved_conflicts: List[str] = Field(..., description="Key unresolved conflicts identified during debate")
    debate_confidence: int = Field(..., ge=0, le=100, description="Consensus debate confidence in the range [0, 100]")


class GuardrailOutput(BaseModel):
    """Represents the output of the Psychological Guardrail layer."""

    model_config = ConfigDict(extra="ignore")

    ticker: str = Field(..., description="The stock ticker symbol")
    raw_confidence: int = Field(..., ge=0, le=100, description="Original aggregated confidence score [0, 100]")
    disagreement_score: float = Field(..., ge=0.0, le=1.0, description="Disagreement among analysts [0.0, 1.0]")
    subjectivity_score: float = Field(..., ge=0.0, le=1.0, description="Subjectivity/sentiment score [0.0, 1.0]")
    herding_flag: bool = Field(..., description="True if potential herding/crowding is detected")
    overconfidence_flag: bool = Field(..., description="True if overconfidence warning is triggered")
    calibrated_confidence: int = Field(..., ge=0, le=100, description="Recalibrated confidence score [0, 100]")
    confidence_multiplier: float = Field(..., ge=0.0, le=1.0, description="Risk sizing multiplier [0.0, 1.0]")
    risk_flags: List[str] = Field(..., description="List of active psychological risk warning flags")
    reasoning: str = Field(..., description="Analysis reasoning explaining the guardrail decision")


class MetaLabelOutput(BaseModel):
    """Represents the final trade permissioning/reduction label."""

    model_config = ConfigDict(extra="ignore")

    ticker: str = Field(..., description="The stock ticker symbol")
    allow_trade: bool = Field(..., description="True if a trade is permitted to execute")
    size_multiplier: float = Field(..., ge=0.0, le=1.0, description="Sizing scaling factor in the range [0.0, 1.0]")
    label: Literal["allow", "reduce", "suppress", "hold_only"] = Field(..., description="The meta trade label")
    reasoning: str = Field(..., description="Explanation for the assigned meta label")


class HybridDecisionTrace(BaseModel):
    """A complete structured trace of the hybrid decision path for a single ticker."""

    model_config = ConfigDict(extra="ignore")

    ticker: str = Field(..., description="The stock ticker symbol")
    timestamp: datetime | None = None
    regime: Optional[RegimeClassification] = Field(None, description="Market regime classification details")
    selected_agents: List[str] = Field(default_factory=list, description="IDs of analysts selected for execution")
    debate: Optional[DebateOutput] = Field(None, description="Safe debate output details")
    guardrails: Optional[GuardrailOutput] = Field(None, description="Psychological guardrail details")
    meta_label: Optional[MetaLabelOutput] = Field(None, description="Final meta-labeler output details")
    reasoning_summary: str | None = None
