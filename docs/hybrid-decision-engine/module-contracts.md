# Module Contracts for Hybrid Decision Engine

## Purpose

This file defines the implementation contracts for the Graph-of-Agents, Safe Debate, Psychological Guardrail, Risk-Constrained Portfolio Manager, and Backtest Reflection layers.

The AI developer agent must treat these contracts as boundary rules. Do not bypass deterministic risk controls. Do not allow free-form LLM text to directly mutate portfolio state.

## 1. Shared Schema Requirements

Create shared Pydantic models in:

```text
src/schemas/hybrid.py
```

Recommended models:

```python
class RegimeClassification(BaseModel):
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
    ]
    confidence: int
    reasoning: str

class AgentSelection(BaseModel):
    ticker: str
    selected_agents: list[str]
    excluded_agents: list[str]
    selection_reasoning: dict[str, str]

class ThesisOutput(BaseModel):
    ticker: str
    stance: Literal["bullish", "bearish", "neutral"]
    confidence: int
    thesis: str
    evidence: list[str]
    risks: list[str]

class DebateOutput(BaseModel):
    ticker: str
    bull_case: str
    bear_case: str
    risk_red_team: str
    unresolved_conflicts: list[str]
    debate_confidence: int

class GuardrailOutput(BaseModel):
    ticker: str
    raw_confidence: int
    disagreement_score: float
    subjectivity_score: float
    herding_flag: bool
    overconfidence_flag: bool
    calibrated_confidence: int
    confidence_multiplier: float
    risk_flags: list[str]
    reasoning: str

class MetaLabelOutput(BaseModel):
    ticker: str
    allow_trade: bool
    size_multiplier: float
    label: Literal["allow", "reduce", "suppress", "hold_only"]
    reasoning: str

class HybridDecisionTrace(BaseModel):
    ticker: str
    regime: RegimeClassification | None
    selected_agents: list[str]
    debate: DebateOutput | None
    guardrails: GuardrailOutput | None
    meta_label: MetaLabelOutput | None
```

## 2. Market Regime Classifier

Suggested file:

```text
src/graph/regime_classifier.py
```

Responsibilities:

- classify current ticker/date-window context
- prefer deterministic features where possible
- optionally use LLM summary only as explanatory context

Inputs:

- ticker
- start_date
- end_date
- price history
- volatility metrics
- trend metrics
- news/sentiment summary if available

Outputs:

- `RegimeClassification`

Forbidden:

- must not produce trade actions
- must not change portfolio state
- must not override risk limits

Initial deterministic regime rules may include:

```text
high realized volatility -> high_volatility
strong trend + low drawdown -> momentum
large recent gap/news count spike -> news_shock
negative trend + high volatility -> risk_off
valuation disagreement + high multiple -> valuation_stress
```

## 3. Adaptive GoA Agent Selector

Suggested file:

```text
src/graph/agent_selector.py
```

Responsibilities:

- select top K analysts for each ticker
- use analyst metadata from `src/utils/analysts.py`
- support static mode fallback
- reduce token use by avoiding irrelevant agents

Inputs:

- ticker context
- regime classification
- available analyst config
- optional user-selected analyst list
- max_agents

Outputs:

- `AgentSelection`

Rules:

- If user explicitly selected analysts, respect user selection unless adaptive mode is disabled.
- If no selection exists, choose agents based on regime and ticker context.
- Always include at least one risk/valuation-aware perspective when possible.

Suggested mapping:

```text
momentum -> technical_analyst, growth_analyst, sentiment_analyst, stanley_druckenmiller
valuation_stress -> valuation_analyst, aswath_damodaran, ben_graham, michael_burry
news_shock -> news_sentiment_analyst, sentiment_analyst, technical_analyst, bill_ackman
risk_off -> michael_burry, stanley_druckenmiller, valuation_analyst, fundamentals_analyst
unknown -> valuation_analyst, fundamentals_analyst, technical_analyst, sentiment_analyst
```

Forbidden:

- must not call LLM unless explicitly needed
- must not execute trades

## 4. Safe Debate Layer

Suggested package:

```text
src/agents/debate/
```

Suggested agents:

```text
bull_researcher.py
bear_researcher.py
risk_red_team.py
consensus.py
```

Responsibilities:

- convert raw analyst signals into competing theses
- force explicit counterargument generation
- identify unresolved conflicts
- produce structured debate output

Inputs:

- analyst signals
- ticker
- market regime
- portfolio context

Outputs:

- `DebateOutput`

Required debate roles:

1. Bull Researcher
   - builds strongest long thesis
   - must cite agent signals supporting upside

2. Bear Researcher
   - builds strongest avoid/short thesis
   - must cite valuation, trend, risk, or sentiment concerns

3. Risk Red-Team
   - attacks both bull and bear cases
   - identifies failure modes and missing evidence

4. Consensus Agent
   - summarizes dominant thesis
   - preserves minority report
   - must not output unconstrained quantity

Forbidden:

- no final quantity
- no direct portfolio mutation
- no broker/execution behavior

## 5. Psychological Guardrail Layer

Suggested file:

```text
src/agents/psychological_guardrail.py
```

Responsibilities:

- calculate disagreement score
- estimate subjectivity/herding risk
- penalize overconfidence
- produce calibrated confidence placeholder
- pass confidence multiplier to risk/portfolio layers

Inputs:

- raw analyst signals
- debate output
- historical calibration data if available

Outputs:

- `GuardrailOutput`

Initial implementation should be deterministic where possible:

```text
signal disagreement = 1 - dominant_signal_weight / total_signal_weight
confidence dispersion = standard deviation of confidence values
subjectivity score = simple lexicon or heuristic count of subjective/emotional terms
calibrated confidence = raw confidence * confidence_multiplier
```

Recommended confidence multiplier:

```text
base = 1.0
if disagreement > 0.45 -> base *= 0.50
elif disagreement > 0.30 -> base *= 0.75
if subjectivity_score > threshold -> base *= 0.85
if confidence_dispersion > threshold -> base *= 0.85
clamp between 0.10 and 1.00
```

Forbidden:

- must not increase confidence above raw confidence in the first version
- must not authorize trades directly

## 6. Meta-Labeler

Suggested file:

```text
src/agents/meta_labeler.py
```

Responsibilities:

- decide whether an otherwise valid signal should be allowed, reduced, suppressed, or hold-only
- convert guardrail output into a deterministic trade permission signal

Inputs:

- consensus/debate output
- guardrail output
- regime classification
- risk metrics

Outputs:

- `MetaLabelOutput`

Suggested rules:

```text
calibrated_confidence < 35 -> suppress
high disagreement + high volatility -> hold_only
moderate disagreement -> reduce with size_multiplier 0.50-0.75
clean signal + normal volatility -> allow
```

Forbidden:

- must not specify final share quantity
- must not bypass risk manager

## 7. Risk-Constrained Portfolio Manager Integration

Existing files:

```text
src/agents/risk_manager.py
src/agents/portfolio_manager.py
```

Required integration:

- Risk manager should optionally consume guardrail/meta-label outputs.
- Risk manager should apply additional multipliers to `remaining_position_limit`.
- Portfolio manager should treat meta-label suppression as a hard action constraint.

Suggested risk formula:

```python
combined_limit_pct = (
    vol_adjusted_limit_pct
    * corr_multiplier
    * disagreement_multiplier
    * drawdown_multiplier
    * meta_label_multiplier
)
```

Suggested portfolio behavior:

```text
if meta_label.label in ["suppress", "hold_only"]:
    allowed_actions = {"hold": 0}
```

Forbidden:

- never let LLM override `allowed_actions`
- never let LLM exceed max quantity

## 8. CPPI-Style Drawdown Guardrail

Suggested file:

```text
src/risk/drawdown_guardrail.py
```

Responsibilities:

- compute protective floor
- compute cushion
- produce risk exposure scalar

Inputs:

- initial capital
- current portfolio value
- floor_pct
- multiplier

Outputs:

```python
class DrawdownGuardrailOutput(BaseModel):
    floor_value: float
    cushion: float
    max_risky_exposure: float
    drawdown_multiplier: float
    breached_floor: bool
```

Rules:

```text
if portfolio_value <= floor_value -> drawdown_multiplier = 0.0
if cushion small -> reduce multiplier
if portfolio makes new high and TIPP mode enabled -> ratchet floor upward
```

## 9. Backtest Reflection Recorder

Suggested package:

```text
src/reflection/
```

Responsibilities:

- record structured traces during backtests
- evaluate later outcomes
- compute agent attribution and calibration data

Initial storage options:

- JSONL file under `.runs/` or `data/reflection/`
- SQLite later if needed

Required record fields:

```text
date
ticker
regime
selected_agents
raw_signals
debate_output
guardrail_output
meta_label
final_decision
executed_quantity
portfolio_value
future_return_1d
future_return_5d
future_return_20d
max_drawdown_after_trade
```

Forbidden:

- do not automatically rewrite prompts from reflection records
- do not leak future returns into same-day decisions

## 10. Backwards Compatibility

All new features must be feature-flagged.

Default CLI/backtester behavior should remain compatible with existing commands unless the user explicitly enables hybrid mode.

Existing result keys must remain:

```text
decisions
analyst_signals
```

New hybrid metadata should be additive.
