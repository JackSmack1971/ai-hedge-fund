# Implementation Roadmap

## Goal

Implement a practical hybrid decision layer for the current AI Hedge Fund codebase:

```text
Graph-of-Agents + Safe Debate + Psychological Guardrails + Risk-Constrained Portfolio Manager + Backtest Reflection
```

This roadmap is optimized for an AI coding agent. Each phase should be implemented in small, reviewable commits with tests.

## Phase 0 — Baseline Preservation

### Objective

Ensure the current CLI and backtester still run before hybrid features are added.

### Tasks

1. Run or create smoke tests for:
   - `src/main.py`
   - `src/backtester.py`
   - `src/agents/risk_manager.py`
   - `src/agents/portfolio_manager.py`
2. Confirm existing result shape:
   - `decisions`
   - `analyst_signals`
3. Do not change existing default behavior.

### Definition of Done

- Existing CLI commands still work.
- Existing backtester still works.
- No hybrid feature runs unless enabled.

## Phase 1 — Shared Hybrid Schemas

### Objective

Create structured Pydantic schemas for all new hybrid outputs.

### Files

```text
src/schemas/hybrid.py
```

### Tasks

1. Add schemas from `module-contracts.md`.
2. Use strict types for labels and regimes.
3. Add serialization helpers if needed.
4. Add unit tests for valid/invalid schema construction.

### Definition of Done

- All schemas import cleanly.
- Invalid labels fail validation.
- Models can be serialized to JSON.

## Phase 2 — Deterministic Guardrail Utilities

### Objective

Implement deterministic utility functions before adding new LLM agents.

### Files

```text
src/risk/disagreement.py
src/risk/drawdown_guardrail.py
src/risk/sizing.py
```

### Tasks

1. Implement signal disagreement score.
2. Implement confidence multiplier calculation.
3. Implement CPPI-style drawdown multiplier.
4. Implement optional fractional Kelly helper, capped and disabled by default.

### Definition of Done

- Disagreement score is deterministic.
- Drawdown guardrail returns zero exposure at/below floor.
- No LLM calls are required.
- Unit tests cover edge cases.

## Phase 3 — Psychological Guardrail Agent

### Objective

Add a guardrail layer that converts raw analyst confidence into calibrated confidence and risk flags.

### Files

```text
src/agents/psychological_guardrail.py
```

### Tasks

1. Read `state["data"]["analyst_signals"]`.
2. For each ticker, compute:
   - raw confidence aggregate
   - disagreement score
   - confidence dispersion
   - subjectivity/herding heuristic
   - confidence multiplier
   - calibrated confidence
3. Store results in:

```python
state["data"]["hybrid"]["guardrails"]
```

4. Return state without mutating portfolio.

### Definition of Done

- Guardrail agent can run after analysts.
- It never outputs final trade quantity.
- It is deterministic except optional LLM explanation.

## Phase 4 — Consensus and Basic Debate Layer

### Objective

Add a minimal Safe Debate implementation.

### Files

```text
src/agents/debate/bull_researcher.py
src/agents/debate/bear_researcher.py
src/agents/debate/risk_red_team.py
src/agents/debate/consensus.py
```

### Recommended First Version

Implement only `consensus.py` first.

Then add bull/bear/risk debate once the consensus layer is stable.

### Tasks

1. Build `consensus_agent` that reads analyst signals.
2. Produce structured summary by ticker:
   - dominant thesis
   - minority thesis
   - unresolved conflicts
   - consensus confidence
3. Store in:

```python
state["data"]["hybrid"]["consensus"]
```

4. Add optional LLM-based bull/bear/risk debate behind `debate_mode`.

### Definition of Done

- Consensus output is structured.
- Existing risk manager still receives analyst signals.
- Portfolio manager still receives constrained allowed actions.

## Phase 5 — Meta-Labeler

### Objective

Add a trade suppression/reduction layer before risk sizing.

### Files

```text
src/agents/meta_labeler.py
```

### Tasks

1. Read guardrail output and consensus output.
2. Assign one label per ticker:
   - `allow`
   - `reduce`
   - `suppress`
   - `hold_only`
3. Compute `size_multiplier`.
4. Store in:

```python
state["data"]["hybrid"]["meta_labels"]
```

### Definition of Done

- Low confidence can suppress a trade.
- High disagreement can force hold-only.
- Size multiplier is bounded between 0.0 and 1.0 in first version.

## Phase 6 — Risk Manager Integration

### Objective

Make the existing risk manager consume hybrid guardrails without breaking old behavior.

### Files

```text
src/agents/risk_manager.py
```

### Tasks

1. Read optional hybrid metadata:

```python
hybrid = state["data"].get("hybrid", {})
```

2. For each ticker, read:
   - guardrail confidence multiplier
   - meta-label size multiplier
   - drawdown multiplier if available
3. Multiply existing `combined_limit_pct` by these values.
4. Include the hybrid multipliers in risk reasoning.

### Definition of Done

- If hybrid metadata is missing, risk manager behaves exactly as before.
- If `meta_label` is suppress/hold_only, remaining position limit becomes 0.
- Risk reasoning exposes applied multipliers.

## Phase 7 — Portfolio Manager Integration

### Objective

Make the existing portfolio manager respect meta-label hard constraints.

### Files

```text
src/agents/portfolio_manager.py
```

### Tasks

1. Read optional hybrid meta-labels.
2. Before LLM final decision, constrain allowed actions:

```text
suppress/hold_only -> {"hold": 0}
reduce -> apply size multiplier to max quantities
allow -> normal behavior
```

3. Keep all existing deterministic max quantity checks.

### Definition of Done

- LLM cannot bypass suppressed tickers.
- LLM cannot exceed reduced max quantity.
- Existing default behavior remains intact.

## Phase 8 — Adaptive GoA Agent Selection

### Objective

Select relevant analysts dynamically instead of always running every analyst.

### Files

```text
src/graph/regime_classifier.py
src/graph/agent_selector.py
src/main.py
src/cli/input.py
```

### Tasks

1. Add CLI flags:
   - `--goa-mode static|adaptive`
   - `--max-agents N`
2. Implement deterministic regime classifier.
3. Implement agent selector using `ANALYST_CONFIG`.
4. Modify workflow construction to use selected agents.

### Definition of Done

- Static mode matches existing behavior.
- Adaptive mode selects fewer agents.
- Selected agents are recorded in hybrid trace.

## Phase 9 — Backtest Reflection Recorder

### Objective

Record structured decision traces for future evaluation.

### Files

```text
src/reflection/recorder.py
src/reflection/schemas.py
src/backtesting/engine.py
```

### Tasks

1. Add optional reflection recording flag.
2. Record each decision step to JSONL.
3. Include future outcome placeholders first.
4. Add evaluator later to fill 1d/5d/20d returns once data is available.

### Definition of Done

- Backtest can produce a trace file.
- Trace file includes analyst, debate, guardrail, risk, and final decision metadata.
- No future data is used during same-day decision-making.

## Phase 10 — Evaluation and Reporting

### Objective

Measure whether the hybrid system improves behavior.

### Metrics

Track:

- CAGR
- Sharpe ratio
- Sortino ratio
- max drawdown
- turnover
- win rate
- average confidence
- expected calibration error proxy
- suppressed-trade outcome analysis
- agent contribution score
- regime-specific performance

### Definition of Done

- Backtest output compares baseline vs hybrid mode.
- Reflection logs can identify which agents helped or hurt.
- Guardrail suppression decisions can be audited.

## Recommended Build Order Summary

```text
1. schemas
2. deterministic risk utilities
3. psychological guardrail
4. consensus agent
5. meta-labeler
6. risk manager integration
7. portfolio manager integration
8. adaptive GoA selector
9. debate layer expansion
10. reflection recorder
```

## Hard Rule

Do not implement live trading. Do not add broker integrations. Do not allow LLM-generated quantities to bypass deterministic constraints.
