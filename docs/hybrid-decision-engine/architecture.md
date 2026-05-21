# Hybrid Decision Engine Architecture

## 1. Architectural Intent

The Hybrid Decision Engine upgrades the current AI Hedge Fund architecture from a static analyst fan-out model into an adaptive, debate-driven, risk-constrained research pipeline.

The design is inspired by the uploaded research document, which argues for a four-pillar architecture:

1. LLM thesis generation and debate
2. Psychology guardrails for bias, disagreement, and calibration
3. Mathematical validation and sizing
4. Financial execution and drawdown discipline

For this codebase, the institutional concept must be simplified into a local research/backtesting system.

## 2. Existing Architecture

The current core workflow is roughly:

```text
start_node
  -> selected analyst agents
  -> risk_management_agent
  -> portfolio_manager
  -> END
```

Current strengths:

- The analyst registry is centralized in `src/utils/analysts.py`.
- The LangGraph workflow is created in `src/main.py`.
- Analyst signals are stored in `state["data"]["analyst_signals"]`.
- `risk_management_agent` computes position limits using price, volatility, and correlation data.
- `portfolio_management_agent` computes deterministic allowed actions before asking an LLM for the final decision.

Current limitation:

- Analysts mostly operate in parallel.
- There is no formal critique/debate layer.
- There is no disagreement or bias penalty before risk sizing.
- Confidence is not empirically calibrated.
- Backtests do not yet create structured reflection memory for future evaluation.

## 3. Target Architecture

```text
Ticker + Portfolio + Date Window
        |
        v
Market Regime Classifier
        |
        v
Adaptive Graph-of-Agents Selector
        |
        v
Selected Analyst Agents
        |
        v
Safe Debate Layer
  - Bull Thesis Agent
  - Bear Thesis Agent
  - Risk Red-Team Agent
        |
        v
Consensus Agent
        |
        v
Psychological Guardrail Layer
  - disagreement score
  - subjectivity/herding score
  - confidence calibration
  - base-rate penalty placeholder
        |
        v
Meta-Labeler
  - allow_trade
  - suppress_trade
  - size_multiplier
        |
        v
Risk Manager
  - volatility limit
  - correlation limit
  - disagreement multiplier
  - drawdown/CPPI multiplier
        |
        v
Constrained Portfolio Manager
  - allowed actions
  - max quantity
  - final decision JSON
        |
        v
Backtest Engine + Reflection Recorder
```

## 4. Required Design Invariants

### 4.1 LLMs Cannot Execute Trades

LLM agents may emit:

- signal direction
- confidence
- thesis
- counter-thesis
- uncertainty estimate
- risk flags
- suggested action

LLMs must not directly mutate portfolio state.

### 4.2 Math and Risk Own Sizing

Position size must be constrained by deterministic calculations:

- available cash
- current position
- current price
- volatility-adjusted limit
- correlation-adjusted limit
- disagreement-adjusted limit
- drawdown guardrail
- portfolio-level exposure cap

### 4.3 Debate Before Consensus

When GoA mode is enabled, raw analyst outputs should not go straight to the portfolio manager. They should pass through a structured synthesis layer:

```text
raw analyst signals -> bull/bear/risk critique -> consensus/meta-label
```

### 4.4 Confidence Is Not Truth

Agent confidence must be treated as an uncalibrated raw input. Before it reaches risk sizing, it should be adjusted by:

- inter-agent disagreement
- subjectivity/herding score
- historical base-rate placeholder
- backtest calibration data when available

### 4.5 Backtests Must Become Evidence

Every backtest step should optionally record structured decision evidence:

- date
- ticker
- selected agents
- raw signals
- debate output
- guardrail scores
- final decision
- executed quantity
- subsequent return windows
- drawdown after trade
- whether the thesis was directionally correct

This enables later confidence calibration and agent attribution.

## 5. Recommended New Package Layout

```text
src/graph/
  agent_selector.py
  regime_classifier.py
  debate_graph.py

src/agents/
  debate/
    bull_researcher.py
    bear_researcher.py
    risk_red_team.py
    consensus.py
  psychological_guardrail.py
  meta_labeler.py

src/risk/
  disagreement.py
  drawdown_guardrail.py
  sizing.py

src/reflection/
  recorder.py
  evaluator.py
  schemas.py

src/schemas/
  hybrid.py
```

## 6. Minimal First Integration

The first integration should avoid deep rewrites.

Recommended minimal graph change:

```text
start_node
  -> selected analyst agents
  -> consensus_agent
  -> psychological_guardrail_agent
  -> risk_management_agent
  -> portfolio_manager
  -> END
```

Then add Safe Debate and adaptive graph selection behind feature flags.

## 7. Feature Flags

Add runtime configuration options:

```text
--goa-mode static|adaptive
--debate-mode off|basic|full
--guardrails off|basic|strict
--reflection off|record
--drawdown-guardrail off|cppi
```

Default behavior should preserve the existing app unless explicitly enabled.

## 8. First-Class Outputs

When enabled, the final result should expose:

```json
{
  "decisions": {},
  "analyst_signals": {},
  "hybrid": {
    "regime": {},
    "selected_agents": {},
    "debate": {},
    "guardrails": {},
    "meta_labels": {},
    "reflection_ids": []
  }
}
```

Existing consumers should continue to work if they only read `decisions` and `analyst_signals`.
