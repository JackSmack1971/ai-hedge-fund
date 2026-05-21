# PRD: Hybrid Decision Engine Integration

## Product Name

Hybrid Decision Engine for AI Hedge Fund

## Status

Planning / Ready for Implementation Decomposition

## Owner

JackSmack1971

## Repository

`JackSmack1971/ai-hedge-fund-forked`

## 1. Product Summary

The Hybrid Decision Engine upgrades the existing AI Hedge Fund research/backtesting application into a safer, more auditable, more adaptive decision system built around five core capabilities:

1. Graph-of-Agents adaptive analyst selection
2. Safe Debate thesis confrontation
3. Psychological Guardrails for disagreement, overconfidence, and bias detection
4. Risk-Constrained Portfolio Management with deterministic authority
5. Backtest Reflection for attribution, calibration, and future improvement

The system remains an educational and research-oriented local application. It must not become a live trading engine. LLMs may reason, critique, debate, summarize, and produce structured signals, but deterministic code must retain final authority over trade admissibility, sizing, risk, drawdown limits, and portfolio state mutation.

## 2. Problem Statement

The current codebase already supports multiple analyst agents, a risk manager, a portfolio manager, and a backtester. However, the current architecture is primarily a static analyst fan-out model:

```text
start_node
  -> selected analyst agents
  -> risk_management_agent
  -> portfolio_manager
  -> END
```

This creates several limitations:

- Analysts do not formally challenge one another.
- All selected analysts may run even when only a subset is relevant.
- Confidence scores are treated as raw signal metadata rather than calibrated probabilities.
- Disagreement is visible but not systematically converted into risk reduction.
- The system lacks a formal trade suppression layer before position sizing.
- Backtests do not yet produce structured decision memory for future evaluation.
- The system cannot yet answer which agents helped, hurt, or overfit in specific regimes.

## 3. Product Vision

The target product is a hybrid investment research simulator where:

```text
LLMs generate and debate theses.
Psychological guardrails audit confidence and disagreement.
Mathematical risk code sizes and constrains exposure.
Portfolio logic enforces admissible actions.
Backtests produce structured learning traces.
```

The practical product identity is:

> An adaptive behavioral-finance Graph-of-Agents research platform with deterministic risk-constrained portfolio construction.

## 4. Design Principles

### 4.1 LLMs Reason, Math Decides

LLMs may produce:

- directional signals
- theses
- counter-theses
- confidence estimates
- uncertainty explanations
- risk flags
- debate summaries

LLMs must not directly:

- mutate cash
- mutate positions
- set final unconstrained quantity
- bypass allowed actions
- override risk limits
- bypass drawdown floors

### 4.2 Fail Closed

Uncertainty, missing data, high disagreement, malformed LLM output, or guardrail failure should reduce risk, not increase it.

### 4.3 Backward Compatibility First

Baseline CLI, backtester, and web flows must continue to work when hybrid mode is disabled.

### 4.4 Feature-Flag Everything

All hybrid behavior must be optional until validated.

### 4.5 Atomic Implementation

Each task must be independently implementable, testable, and reviewable. No task should require a large architectural rewrite before providing value.

## 5. Goals

### 5.1 MVP Goals

- Add shared structured schemas for hybrid outputs.
- Add deterministic disagreement and drawdown utilities.
- Add a psychological guardrail layer.
- Add a consensus layer.
- Add a meta-labeler that can allow, reduce, suppress, or force hold-only.
- Integrate guardrail/meta-label outputs into risk and portfolio constraints.
- Add basic reflection recording during backtests.
- Preserve existing baseline behavior.

### 5.2 Post-MVP Goals

- Add adaptive GoA analyst selection.
- Add market regime classification.
- Add full Safe Debate with bull, bear, and risk red-team agents.
- Add confidence calibration reports.
- Add agent attribution and regime-specific performance analysis.
- Add UI visibility for hybrid traces.
- Add optional advanced allocation modules such as fractional Kelly and signal-aware portfolio weighting.

## 6. Non-Goals

The following are explicitly out of scope for MVP:

- live trading
- broker integrations
- real-money execution
- reinforcement-learning execution agents
- SAPPO implementation
- full institutional Black-Litterman optimizer
- paid institutional data integrations
- automatic prompt self-modification
- automatic fine-tuning
- hidden network-dependent tests

## 7. User Stories

### 7.1 Research User

As a research user, I want to enable hybrid mode so that I can see not only a final trade decision, but also the debate, disagreement, confidence adjustment, and risk constraints that led to it.

### 7.2 Backtest User

As a backtest user, I want the system to record decision traces so that I can later evaluate which agents and guardrails improved or degraded performance.

### 7.3 Safety-Oriented User

As a safety-oriented user, I want high-disagreement or low-confidence trades to be reduced or suppressed before the portfolio manager can act on them.

### 7.4 Developer Agent

As an AI developer agent, I need sequential atomic tasks with acceptance criteria so that I can implement the hybrid architecture without breaking existing CLI, API, backtesting, or portfolio safety behavior.

## 8. Success Metrics

### 8.1 Functional Metrics

- Hybrid mode can run without breaking baseline mode.
- Each ticker receives a structured hybrid trace when enabled.
- Meta-label suppression forces hold.
- Reduced meta-labels reduce maximum allowed quantities.
- Risk manager records applied hybrid multipliers.
- Backtest reflection records are created when enabled.

### 8.2 Backtest Metrics

Track baseline versus hybrid mode:

- CAGR
- Sharpe ratio
- Sortino ratio
- max drawdown
- turnover
- win rate
- average confidence before guardrails
- average confidence after guardrails
- suppressed trade count
- realized outcome of suppressed trades
- regime-specific performance
- agent contribution score

### 8.3 Safety Metrics

- Zero cases where LLM output bypasses deterministic quantity caps.
- Zero cases where suppressed/hold-only labels execute risky trades.
- Zero cases where future returns leak into current decision generation.
- Zero crashes when hybrid metadata is absent.

## 9. MVP Scope

The MVP is complete when the following flow works in CLI/backtester mode behind feature flags:

```text
selected analyst agents
  -> consensus agent
  -> psychological guardrail
  -> meta-labeler
  -> risk manager with hybrid multipliers
  -> portfolio manager with meta-label constraints
  -> backtest reflection recorder
```

Adaptive GoA selection and full Safe Debate may begin post-MVP unless trivial to include safely.

## 10. Feature Flags

Add or prepare for the following flags:

```text
--hybrid-mode off|basic|full
--guardrails off|basic|strict
--debate-mode off|consensus|full
--goa-mode static|adaptive
--reflection off|record
--drawdown-guardrail off|cppi
--max-agents N
```

MVP may initially implement only:

```text
--hybrid-mode off|basic
--guardrails off|basic
--reflection off|record
```

## 11. Sequential Atomic Tasks

The following tasks are designed to avoid critical blockers. Each task should be implementable as a small commit or PR.

---

# Phase 0: Baseline Inventory and Safety Lock

## Task 0.1 — Confirm Baseline Entry Points

**Type:** Documentation / Verification  
**Files:** None or `docs/hybrid-decision-engine/baseline-inventory.md`  
**Depends on:** None

### Work

- Identify baseline CLI entry point.
- Identify baseline backtester entry point.
- Identify baseline workflow creation function.
- Identify baseline risk manager and portfolio manager files.
- Identify baseline result shape.

### Acceptance Criteria

- A short baseline inventory exists or is included in implementation notes.
- Developer can state how current decisions flow from analyst agents to risk manager to portfolio manager.

## Task 0.2 — Add Baseline Smoke Test Plan

**Type:** Test planning  
**Files:** `docs/hybrid-decision-engine/testing-and-validation.md` or test stubs  
**Depends on:** Task 0.1

### Work

- Define minimal smoke tests for baseline importability.
- Define minimal smoke tests for risk and portfolio deterministic helper functions.

### Acceptance Criteria

- Smoke test plan exists.
- No production code behavior changes.

## Task 0.3 — Create Hybrid Implementation Branch

**Type:** Repo hygiene  
**Files:** None  
**Depends on:** None

### Work

- Create branch such as `feature/hybrid-decision-engine-mvp`.
- Keep main branch protected from large direct implementation commits.

### Acceptance Criteria

- Branch exists.
- No source files changed.

---

# Phase 1: Shared Schemas and Type Contracts

## Task 1.1 — Create Hybrid Schema Package

**Type:** Code  
**Files:** `src/schemas/__init__.py`, `src/schemas/hybrid.py`  
**Depends on:** None

### Work

- Add schema package if missing.
- Add Pydantic models for hybrid outputs.

### Acceptance Criteria

- `src.schemas.hybrid` imports without side effects.
- No existing workflow imports are changed.

## Task 1.2 — Add RegimeClassification Schema

**Type:** Code  
**Files:** `src/schemas/hybrid.py`  
**Depends on:** Task 1.1

### Work

Add model:

```python
RegimeClassification
```

Fields:

- `regime`
- `confidence`
- `reasoning`

### Acceptance Criteria

- Valid regimes serialize to JSON.
- Invalid regimes fail validation.

## Task 1.3 — Add AgentSelection Schema

**Type:** Code  
**Files:** `src/schemas/hybrid.py`  
**Depends on:** Task 1.1

### Work

Add model:

```python
AgentSelection
```

Fields:

- `ticker`
- `selected_agents`
- `excluded_agents`
- `selection_reasoning`

### Acceptance Criteria

- Empty excluded list is valid.
- Selected agents must serialize cleanly.

## Task 1.4 — Add Thesis and Debate Schemas

**Type:** Code  
**Files:** `src/schemas/hybrid.py`  
**Depends on:** Task 1.1

### Work

Add models:

```python
ThesisOutput
DebateOutput
```

### Acceptance Criteria

- Thesis stance is restricted to bullish, bearish, neutral.
- Debate output can include unresolved conflicts.

## Task 1.5 — Add Guardrail Schema

**Type:** Code  
**Files:** `src/schemas/hybrid.py`  
**Depends on:** Task 1.1

### Work

Add model:

```python
GuardrailOutput
```

Fields:

- `ticker`
- `raw_confidence`
- `disagreement_score`
- `subjectivity_score`
- `herding_flag`
- `overconfidence_flag`
- `calibrated_confidence`
- `confidence_multiplier`
- `risk_flags`
- `reasoning`

### Acceptance Criteria

- Confidence values validate between 0 and 100 if validators are added.
- Multipliers validate within safe bounds if validators are added.

## Task 1.6 — Add MetaLabel Schema

**Type:** Code  
**Files:** `src/schemas/hybrid.py`  
**Depends on:** Task 1.1

### Work

Add model:

```python
MetaLabelOutput
```

Labels:

- `allow`
- `reduce`
- `suppress`
- `hold_only`

### Acceptance Criteria

- Invalid label fails validation.
- Size multiplier serializes as float.

## Task 1.7 — Add HybridDecisionTrace Schema

**Type:** Code  
**Files:** `src/schemas/hybrid.py`  
**Depends on:** Tasks 1.2–1.6

### Work

Add model:

```python
HybridDecisionTrace
```

### Acceptance Criteria

- Trace can contain optional `None` fields.
- Trace can be serialized into reflection logs.

## Task 1.8 — Add Schema Unit Tests

**Type:** Test  
**Files:** `tests/test_hybrid_schemas.py`  
**Depends on:** Tasks 1.1–1.7

### Work

- Test valid model creation.
- Test invalid enum values.
- Test JSON serialization.

### Acceptance Criteria

- Tests pass without network access.
- Tests do not require API keys.

---

# Phase 2: Deterministic Risk and Guardrail Utilities

## Task 2.1 — Create Risk Utility Package

**Type:** Code  
**Files:** `src/risk/__init__.py`  
**Depends on:** None

### Work

- Create package for deterministic hybrid risk utilities.

### Acceptance Criteria

- Package imports cleanly.

## Task 2.2 — Implement Signal Normalization Helper

**Type:** Code  
**Files:** `src/risk/disagreement.py`  
**Depends on:** Task 2.1

### Work

Implement helper to normalize analyst signals into a common format:

```python
normalize_signal_payloads(analyst_signals, ticker)
```

### Acceptance Criteria

- Handles missing ticker.
- Handles missing confidence.
- Handles unknown signal values conservatively.

## Task 2.3 — Implement Dominant Signal Weight Calculation

**Type:** Code  
**Files:** `src/risk/disagreement.py`  
**Depends on:** Task 2.2

### Work

Compute weighted totals for bullish, bearish, neutral, and unknown.

### Acceptance Criteria

- Confidence-weighted totals are deterministic.
- Missing values do not crash.

## Task 2.4 — Implement Disagreement Score

**Type:** Code  
**Files:** `src/risk/disagreement.py`  
**Depends on:** Task 2.3

### Work

Implement:

```python
calculate_disagreement_score(signals) -> float
```

Suggested formula:

```text
1 - dominant_signal_weight / total_signal_weight
```

### Acceptance Criteria

- All bullish returns low disagreement.
- Half bullish / half bearish returns high disagreement.
- Empty signals return conservative default.

## Task 2.5 — Implement Confidence Dispersion

**Type:** Code  
**Files:** `src/risk/disagreement.py`  
**Depends on:** Task 2.2

### Work

Compute standard deviation or range of confidence values.

### Acceptance Criteria

- Empty or single-value input returns safe default.
- No numpy dependency required unless already convenient.

## Task 2.6 — Implement Confidence Multiplier

**Type:** Code  
**Files:** `src/risk/disagreement.py`  
**Depends on:** Tasks 2.4–2.5

### Work

Implement:

```python
calculate_confidence_multiplier(disagreement_score, subjectivity_score=0.0, confidence_dispersion=0.0)
```

### Acceptance Criteria

- Multiplier never exceeds 1.0.
- High disagreement reduces multiplier.
- Multiplier is bounded by configured minimum.

## Task 2.7 — Implement Simple Subjectivity Heuristic

**Type:** Code  
**Files:** `src/risk/disagreement.py` or `src/risk/subjectivity.py`  
**Depends on:** Task 2.1

### Work

Implement a lightweight lexicon heuristic for subjective/herding language.

### Acceptance Criteria

- Function accepts text and returns 0.0–1.0.
- Empty text returns 0.0.
- No external lexicon dependency required for MVP.

## Task 2.8 — Implement CPPI Drawdown Guardrail Output

**Type:** Code  
**Files:** `src/risk/drawdown_guardrail.py`  
**Depends on:** Task 2.1

### Work

Implement:

```python
calculate_cppi_guardrail(portfolio_value, initial_capital, floor_pct=0.85, multiplier=3.0)
```

### Acceptance Criteria

- At or below floor returns drawdown multiplier 0.0.
- Above floor returns positive cushion.
- Output is deterministic.

## Task 2.9 — Implement Optional TIPP Floor Ratchet Helper

**Type:** Code  
**Files:** `src/risk/drawdown_guardrail.py`  
**Depends on:** Task 2.8

### Work

Implement helper:

```python
calculate_tipp_floor(high_water_mark, floor_pct)
```

### Acceptance Criteria

- Floor rises with high-water mark.
- Floor never exceeds high-water mark.
- Not enabled by default.

## Task 2.10 — Add Risk Utility Unit Tests

**Type:** Test  
**Files:** `tests/test_disagreement.py`, `tests/test_drawdown_guardrail.py`  
**Depends on:** Tasks 2.2–2.9

### Work

- Test signal disagreement edge cases.
- Test confidence multiplier bounds.
- Test CPPI floor behavior.

### Acceptance Criteria

- Tests pass without API keys.
- Tests do not import LangChain or call LLMs.

---

# Phase 3: Hybrid State Container

## Task 3.1 — Define Hybrid State Helper

**Type:** Code  
**Files:** `src/graph/hybrid_state.py`  
**Depends on:** Phase 1

### Work

Implement helper:

```python
ensure_hybrid_state(state) -> dict
```

It should guarantee:

```python
state["data"]["hybrid"]
```

exists with safe nested keys.

### Acceptance Criteria

- Existing states without `hybrid` do not crash.
- Function mutates only the metadata container, not portfolio.

## Task 3.2 — Add Hybrid State Accessors

**Type:** Code  
**Files:** `src/graph/hybrid_state.py`  
**Depends on:** Task 3.1

### Work

Add helpers:

```python
get_guardrail_for_ticker(state, ticker)
get_meta_label_for_ticker(state, ticker)
set_hybrid_value(state, section, ticker, value)
```

### Acceptance Criteria

- Missing keys return `None` or safe default.
- Helpers are side-effect limited.

## Task 3.3 — Add Hybrid State Unit Tests

**Type:** Test  
**Files:** `tests/test_hybrid_state.py`  
**Depends on:** Tasks 3.1–3.2

### Work

- Test missing hybrid state.
- Test setting and retrieving values.

### Acceptance Criteria

- Tests pass without LLMs.

---

# Phase 4: Psychological Guardrail Agent

## Task 4.1 — Create Psychological Guardrail Agent File

**Type:** Code  
**Files:** `src/agents/psychological_guardrail.py`  
**Depends on:** Phases 1–3

### Work

Create agent function skeleton:

```python
psychological_guardrail_agent(state: AgentState, agent_id: str = "psychological_guardrail")
```

### Acceptance Criteria

- Agent imports cleanly.
- Agent returns state shape compatible with LangGraph.
- Agent does not mutate portfolio.

## Task 4.2 — Extract Per-Ticker Analyst Signals

**Type:** Code  
**Files:** `src/agents/psychological_guardrail.py`  
**Depends on:** Task 4.1

### Work

For each ticker, read:

```python
state["data"]["analyst_signals"]
```

### Acceptance Criteria

- Missing signals produce conservative guardrail output.
- No crashes for unknown agent payloads.

## Task 4.3 — Compute Raw Aggregate Confidence

**Type:** Code  
**Files:** `src/agents/psychological_guardrail.py`  
**Depends on:** Task 4.2

### Work

Compute average or weighted average confidence for available signals.

### Acceptance Criteria

- Empty signals result in low raw confidence.
- Confidence is clamped 0–100.

## Task 4.4 — Compute Disagreement and Dispersion

**Type:** Code  
**Files:** `src/agents/psychological_guardrail.py`  
**Depends on:** Task 4.3 and Phase 2

### Work

Use deterministic utilities to compute:

- disagreement score
- confidence dispersion

### Acceptance Criteria

- Output appears in `GuardrailOutput`.

## Task 4.5 — Compute Subjectivity/Herding Heuristic

**Type:** Code  
**Files:** `src/agents/psychological_guardrail.py`  
**Depends on:** Task 4.4

### Work

Aggregate available reasoning/thesis text and compute subjectivity score.

### Acceptance Criteria

- Missing reasoning text returns 0.0 subjectivity.
- High subjectivity can set herding flag.

## Task 4.6 — Produce GuardrailOutput Per Ticker

**Type:** Code  
**Files:** `src/agents/psychological_guardrail.py`  
**Depends on:** Tasks 4.1–4.5

### Work

Create and store:

```python
state["data"]["hybrid"]["guardrails"][ticker]
```

### Acceptance Criteria

- Stored value is JSON-serializable.
- Calibrated confidence is never greater than raw confidence in MVP.

## Task 4.7 — Add Guardrail Agent Unit Tests

**Type:** Test  
**Files:** `tests/test_psychological_guardrail.py`  
**Depends on:** Task 4.6

### Work

- Fake state with aligned signals.
- Fake state with conflicting signals.
- Fake state with missing signals.

### Acceptance Criteria

- Conflicting signals produce lower calibrated confidence.
- Missing signals fail closed.

---

# Phase 5: Consensus Layer MVP

## Task 5.1 — Create Debate Package

**Type:** Code  
**Files:** `src/agents/debate/__init__.py`  
**Depends on:** Phase 1

### Work

Create package for debate agents.

### Acceptance Criteria

- Package imports cleanly.

## Task 5.2 — Create Consensus Agent Skeleton

**Type:** Code  
**Files:** `src/agents/debate/consensus.py`  
**Depends on:** Task 5.1

### Work

Create:

```python
consensus_agent(state: AgentState, agent_id: str = "consensus_agent")
```

### Acceptance Criteria

- Agent returns LangGraph-compatible state.
- Agent does not mutate portfolio.

## Task 5.3 — Implement Deterministic Consensus Summary

**Type:** Code  
**Files:** `src/agents/debate/consensus.py`  
**Depends on:** Task 5.2

### Work

For each ticker:

- count weighted bullish/bearish/neutral signals
- identify dominant signal
- identify minority signal
- identify unresolved conflicts
- produce confidence summary

### Acceptance Criteria

- Works without LLM calls.
- Output is JSON-serializable.

## Task 5.4 — Store Consensus in Hybrid State

**Type:** Code  
**Files:** `src/agents/debate/consensus.py`  
**Depends on:** Task 5.3 and Phase 3

### Work

Store under:

```python
state["data"]["hybrid"]["consensus"][ticker]
```

### Acceptance Criteria

- Existing `analyst_signals` remain unchanged.

## Task 5.5 — Add Consensus Tests

**Type:** Test  
**Files:** `tests/test_consensus_agent.py`  
**Depends on:** Task 5.4

### Work

Test dominant and conflicting signal scenarios.

### Acceptance Criteria

- Dominant signal is identified correctly.
- Conflicts are preserved instead of hidden.

---

# Phase 6: Meta-Labeler MVP

## Task 6.1 — Create Meta-Labeler Agent File

**Type:** Code  
**Files:** `src/agents/meta_labeler.py`  
**Depends on:** Phases 1, 3, 4, 5

### Work

Create agent skeleton:

```python
meta_labeler_agent(state: AgentState, agent_id: str = "meta_labeler")
```

### Acceptance Criteria

- Agent imports cleanly.
- Agent does not mutate portfolio.

## Task 6.2 — Implement Meta-Label Decision Rules

**Type:** Code  
**Files:** `src/agents/meta_labeler.py`  
**Depends on:** Task 6.1

### Work

Rules:

```text
calibrated_confidence < 35 -> suppress
high disagreement >= 0.45 -> hold_only or suppress
moderate disagreement >= 0.30 -> reduce
otherwise -> allow
```

### Acceptance Criteria

- All labels are valid `MetaLabelOutput` labels.
- Size multiplier remains 0.0–1.0.

## Task 6.3 — Store Meta-Labels in Hybrid State

**Type:** Code  
**Files:** `src/agents/meta_labeler.py`  
**Depends on:** Task 6.2

### Work

Store under:

```python
state["data"]["hybrid"]["meta_labels"][ticker]
```

### Acceptance Criteria

- Output is JSON-serializable.

## Task 6.4 — Add Meta-Labeler Tests

**Type:** Test  
**Files:** `tests/test_meta_labeler.py`  
**Depends on:** Task 6.3

### Work

Test suppression, reduction, and allow scenarios.

### Acceptance Criteria

- Low confidence suppresses.
- Moderate risk reduces.
- Clean signal allows.

---

# Phase 7: Workflow Feature Flags

## Task 7.1 — Add Hybrid Config Object

**Type:** Code  
**Files:** `src/graph/hybrid_config.py`  
**Depends on:** None

### Work

Create a simple config model or helper for hybrid settings:

```python
HybridConfig
```

Fields:

- `hybrid_mode`
- `guardrails`
- `debate_mode`
- `reflection`

### Acceptance Criteria

- Defaults disable hybrid behavior.

## Task 7.2 — Add CLI Flag Parsing for Hybrid Mode

**Type:** Code  
**Files:** `src/cli/input.py`  
**Depends on:** Task 7.1

### Work

Add optional flags:

```text
--hybrid-mode off|basic
--guardrails off|basic
--reflection off|record
```

### Acceptance Criteria

- Defaults preserve existing CLI behavior.
- Invalid flags fail gracefully.

## Task 7.3 — Pass Hybrid Config Into Run State

**Type:** Code  
**Files:** `src/main.py`  
**Depends on:** Task 7.2

### Work

Add hybrid config to:

```python
state["metadata"]
```

or:

```python
state["data"]["hybrid_config"]
```

### Acceptance Criteria

- Existing callers without hybrid config still work.

## Task 7.4 — Add Workflow Nodes Behind Feature Flag

**Type:** Code  
**Files:** `src/main.py`  
**Depends on:** Phases 4–6 and Task 7.3

### Work

If hybrid mode is basic, modify workflow:

```text
analysts -> consensus_agent -> psychological_guardrail_agent -> meta_labeler_agent -> risk_manager -> portfolio_manager
```

If hybrid mode is off, preserve current workflow exactly.

### Acceptance Criteria

- Hybrid disabled equals current topology.
- Hybrid enabled inserts new nodes.
- No cyclic graph errors.

## Task 7.5 — Add Workflow Integration Test

**Type:** Test  
**Files:** `tests/test_hybrid_workflow_topology.py`  
**Depends on:** Task 7.4

### Work

Test workflow construction in off and basic modes.

### Acceptance Criteria

- Off mode does not include hybrid nodes.
- Basic mode includes consensus, guardrail, and meta-labeler.

---

# Phase 8: Risk Manager Integration

## Task 8.1 — Add Safe Hybrid Metadata Read in Risk Manager

**Type:** Code  
**Files:** `src/agents/risk_manager.py`  
**Depends on:** Phase 3

### Work

Read:

```python
hybrid = state["data"].get("hybrid", {})
```

### Acceptance Criteria

- Missing hybrid metadata does not crash.
- Baseline behavior unchanged when metadata is absent.

## Task 8.2 — Apply Guardrail Confidence Multiplier

**Type:** Code  
**Files:** `src/agents/risk_manager.py`  
**Depends on:** Task 8.1

### Work

For each ticker, if guardrail exists, multiply risk limit by `confidence_multiplier`.

### Acceptance Criteria

- Multiplier less than 1 reduces position limit.
- Missing multiplier defaults to 1.

## Task 8.3 — Apply Meta-Label Size Multiplier

**Type:** Code  
**Files:** `src/agents/risk_manager.py`  
**Depends on:** Task 8.2

### Work

For each ticker:

```text
allow -> multiplier unchanged
reduce -> apply size_multiplier
suppress/hold_only -> remaining_position_limit = 0
```

### Acceptance Criteria

- Suppression produces zero remaining limit.
- Reduction lowers remaining limit.

## Task 8.4 — Add Hybrid Multipliers to Risk Reasoning

**Type:** Code  
**Files:** `src/agents/risk_manager.py`  
**Depends on:** Task 8.3

### Work

Add to risk reasoning:

- guardrail multiplier
- meta-label multiplier
- final hybrid multiplier
- reason if suppressed

### Acceptance Criteria

- Output remains JSON-serializable.
- Existing output fields remain available.

## Task 8.5 — Add Risk Manager Hybrid Tests

**Type:** Test  
**Files:** `tests/test_risk_manager_hybrid.py`  
**Depends on:** Task 8.4

### Work

Use fake or mocked price data where needed.

### Acceptance Criteria

- No hybrid metadata matches baseline calculation.
- Suppressed ticker gets zero limit.
- Reduced ticker gets lower limit.

---

# Phase 9: Portfolio Manager Integration

## Task 9.1 — Add Safe Meta-Label Read in Portfolio Manager

**Type:** Code  
**Files:** `src/agents/portfolio_manager.py`  
**Depends on:** Phase 3

### Work

Read meta-labels safely from hybrid state.

### Acceptance Criteria

- Missing hybrid metadata does not crash.

## Task 9.2 — Enforce Suppress and Hold-Only Labels

**Type:** Code  
**Files:** `src/agents/portfolio_manager.py`  
**Depends on:** Task 9.1

### Work

Before LLM decision generation:

```text
if label in suppress/hold_only -> allowed_actions = {"hold": 0}
```

### Acceptance Criteria

- LLM cannot buy, sell, short, or cover suppressed tickers.

## Task 9.3 — Apply Reduce Size Multiplier to Allowed Quantities

**Type:** Code  
**Files:** `src/agents/portfolio_manager.py`  
**Depends on:** Task 9.2

### Work

For label `reduce`, scale non-hold max quantities by `size_multiplier`.

### Acceptance Criteria

- Quantity cannot exceed scaled max.
- Quantity floors to integer safely.

## Task 9.4 — Add Portfolio Manager Hybrid Tests

**Type:** Test  
**Files:** `tests/test_portfolio_manager_hybrid.py`  
**Depends on:** Task 9.3

### Work

Test allowed action computation with meta-labels.

### Acceptance Criteria

- Suppress forces hold.
- Reduce scales quantities.
- Allow preserves existing behavior.

---

# Phase 10: Backtest Reflection MVP

## Task 10.1 — Create Reflection Package

**Type:** Code  
**Files:** `src/reflection/__init__.py`  
**Depends on:** None

### Work

Create reflection package.

### Acceptance Criteria

- Package imports cleanly.

## Task 10.2 — Add Reflection Schemas

**Type:** Code  
**Files:** `src/reflection/schemas.py`  
**Depends on:** Phase 1

### Work

Add schema:

```python
ReflectionRecord
```

Fields:

- date
- ticker
- regime
- selected_agents
- raw_signals
- consensus
- guardrails
- meta_label
- risk_output
- final_decision
- executed_quantity
- portfolio_value
- future_return_1d nullable
- future_return_5d nullable
- future_return_20d nullable

### Acceptance Criteria

- Future return fields default to `None`.
- Record serializes to JSON.

## Task 10.3 — Implement JSONL Reflection Recorder

**Type:** Code  
**Files:** `src/reflection/recorder.py`  
**Depends on:** Task 10.2

### Work

Implement:

```python
ReflectionRecorder
```

Methods:

- `write_record(record)`
- `build_record_from_state(...)`

### Acceptance Criteria

- Writes JSONL file.
- Creates directory if missing.
- Does not require database.

## Task 10.4 — Add Reflection Flag to Backtester

**Type:** Code  
**Files:** `src/backtester.py`, `src/backtesting/engine.py`, `src/cli/input.py`  
**Depends on:** Tasks 7.2 and 10.3

### Work

Add `--reflection record` support.

### Acceptance Criteria

- Reflection disabled by default.
- Reflection enabled writes trace records.

## Task 10.5 — Record Decision Trace After Each Backtest Day

**Type:** Code  
**Files:** `src/backtesting/engine.py`  
**Depends on:** Task 10.4

### Work

After decisions and executed trades, record:

- agent output
- decisions
- executed trades
- portfolio value
- hybrid trace if present

### Acceptance Criteria

- No future return fields are populated during same-day decision generation.
- JSONL is append-only.

## Task 10.6 — Add Reflection Tests

**Type:** Test  
**Files:** `tests/test_reflection_recorder.py`  
**Depends on:** Task 10.5

### Work

Test JSONL writing and serialization.

### Acceptance Criteria

- Test uses temp directory.
- No network access required.

---

# Phase 11: MVP End-to-End Validation

## Task 11.1 — Add Hybrid Basic Mode Smoke Test

**Type:** Test  
**Files:** `tests/test_hybrid_basic_smoke.py`  
**Depends on:** Phases 1–10

### Work

Run a minimal fake or mocked workflow with hybrid mode basic.

### Acceptance Criteria

- Hybrid metadata is produced.
- Decisions key still exists.
- Analyst signals key still exists.

## Task 11.2 — Add Baseline Compatibility Smoke Test

**Type:** Test  
**Files:** `tests/test_baseline_compatibility.py`  
**Depends on:** Phases 7–9

### Work

Ensure hybrid disabled path does not require hybrid state.

### Acceptance Criteria

- Baseline workflow construction still works.
- Risk manager and portfolio manager handle missing hybrid metadata.

## Task 11.3 — Manual Backtest Comparison Script

**Type:** Tooling  
**Files:** `scripts/compare_hybrid_backtest.py` or docs command block  
**Depends on:** Phase 10

### Work

Create documented commands for comparing:

```text
baseline
hybrid basic
hybrid basic + reflection
```

### Acceptance Criteria

- Commands are documented.
- Script is optional if time-constrained.

## Task 11.4 — MVP README Update

**Type:** Documentation  
**Files:** `docs/hybrid-decision-engine/README.md` or root README later  
**Depends on:** MVP implementation

### Work

Document:

- how to enable hybrid mode
- what it does
- what it does not do
- where reflection logs are stored

### Acceptance Criteria

- User can run MVP from docs.
- Safety disclaimers remain clear.

## Task 11.5 — MVP Release Gate

**Type:** Review  
**Files:** None  
**Depends on:** Tasks 11.1–11.4

### Work

Review against MVP criteria.

### Acceptance Criteria

- All MVP tests pass.
- Baseline mode works.
- Hybrid mode produces traceable decisions.
- No live trading behavior exists.

---

# Phase 12: Post-MVP Adaptive GoA Selection

## Task 12.1 — Create Regime Classifier File

**Type:** Code  
**Files:** `src/graph/regime_classifier.py`  
**Depends on:** Phase 1

### Work

Create deterministic classifier skeleton.

### Acceptance Criteria

- Imports cleanly.
- Returns `RegimeClassification`.

## Task 12.2 — Add Price-Based Regime Features

**Type:** Code  
**Files:** `src/graph/regime_classifier.py`  
**Depends on:** Task 12.1

### Work

Compute simple features:

- realized volatility
- recent return
- drawdown
- trend direction

### Acceptance Criteria

- Handles insufficient data.
- No LLM required.

## Task 12.3 — Add Deterministic Regime Rules

**Type:** Code  
**Files:** `src/graph/regime_classifier.py`  
**Depends on:** Task 12.2

### Work

Rules for:

- high_volatility
- momentum
- risk_off
- mean_reversion
- unknown

### Acceptance Criteria

- Always returns a valid regime.
- Unknown is safe fallback.

## Task 12.4 — Create Agent Selector File

**Type:** Code  
**Files:** `src/graph/agent_selector.py`  
**Depends on:** Task 12.3

### Work

Create selector using `ANALYST_CONFIG` metadata.

### Acceptance Criteria

- Imports analyst config.
- Does not call LLM.

## Task 12.5 — Implement Regime-to-Agent Mapping

**Type:** Code  
**Files:** `src/graph/agent_selector.py`  
**Depends on:** Task 12.4

### Work

Map regimes to preferred analysts.

### Acceptance Criteria

- Returns at most `max_agents`.
- Always returns at least one analyst if available.

## Task 12.6 — Respect User-Selected Analysts

**Type:** Code  
**Files:** `src/graph/agent_selector.py`  
**Depends on:** Task 12.5

### Work

If user explicitly selects analysts, respect or intersect based on config.

### Acceptance Criteria

- User selection is not silently ignored.
- Adaptive mode can be disabled.

## Task 12.7 — Add GoA CLI Flags

**Type:** Code  
**Files:** `src/cli/input.py`  
**Depends on:** Task 12.6

### Work

Add:

```text
--goa-mode static|adaptive
--max-agents N
```

### Acceptance Criteria

- Static is default.

## Task 12.8 — Integrate Agent Selector Into Workflow Creation

**Type:** Code  
**Files:** `src/main.py`  
**Depends on:** Task 12.7

### Work

Use selected agents from GoA selector when adaptive mode is enabled.

### Acceptance Criteria

- Static workflow remains unchanged.
- Adaptive workflow uses fewer agents.

## Task 12.9 — Record Selected Agents in Hybrid Trace

**Type:** Code  
**Files:** `src/main.py`, `src/graph/hybrid_state.py`  
**Depends on:** Task 12.8

### Work

Store selected agents per ticker or run.

### Acceptance Criteria

- Reflection records include selected agents.

## Task 12.10 — Add GoA Selector Tests

**Type:** Test  
**Files:** `tests/test_agent_selector.py`, `tests/test_regime_classifier.py`  
**Depends on:** Tasks 12.1–12.9

### Work

Test deterministic selection.

### Acceptance Criteria

- Max agent cap is respected.
- Unknown regime returns safe default set.

---

# Phase 13: Post-MVP Safe Debate Expansion

## Task 13.1 — Add Bull Researcher Agent

**Type:** Code  
**Files:** `src/agents/debate/bull_researcher.py`  
**Depends on:** Phase 5

### Work

Create agent that builds strongest bullish thesis from analyst signals.

### Acceptance Criteria

- Outputs structured thesis.
- No trade quantity emitted.

## Task 13.2 — Add Bear Researcher Agent

**Type:** Code  
**Files:** `src/agents/debate/bear_researcher.py`  
**Depends on:** Phase 5

### Work

Create agent that builds strongest bearish/avoid thesis.

### Acceptance Criteria

- Outputs structured thesis.
- Preserves risk/evidence fields.

## Task 13.3 — Add Risk Red-Team Agent

**Type:** Code  
**Files:** `src/agents/debate/risk_red_team.py`  
**Depends on:** Tasks 13.1–13.2

### Work

Create agent that critiques both bull and bear cases.

### Acceptance Criteria

- Identifies failure modes.
- Does not choose final trade quantity.

## Task 13.4 — Add Full Debate Orchestrator

**Type:** Code  
**Files:** `src/graph/debate_graph.py`  
**Depends on:** Tasks 13.1–13.3

### Work

Orchestrate:

```text
bull -> bear -> risk red-team -> consensus
```

or equivalent safe sequence.

### Acceptance Criteria

- Feature-flagged behind `debate-mode full`.
- Basic consensus remains available.

## Task 13.5 — Add Debate Prompt Contracts

**Type:** Documentation / Code  
**Files:** `docs/hybrid-decision-engine/debate-prompts.md` or prompt module  
**Depends on:** Tasks 13.1–13.4

### Work

Document or encode prompts requiring:

- evidence citation from provided data
- explicit uncertainty
- no unconstrained trade sizing

### Acceptance Criteria

- Prompts include forbidden behavior statements.

## Task 13.6 — Add Safe Debate Tests

**Type:** Test  
**Files:** `tests/test_safe_debate.py`  
**Depends on:** Task 13.4

### Work

Test orchestrator with fake structured outputs.

### Acceptance Criteria

- Debate output preserves bull and bear cases.
- Risk red-team output appears in consensus trace.

---

# Phase 14: Post-MVP Drawdown and Sizing Enhancements

## Task 14.1 — Integrate CPPI Guardrail Into Backtest State

**Type:** Code  
**Files:** `src/backtesting/engine.py`, `src/risk/drawdown_guardrail.py`  
**Depends on:** Phase 2 and Phase 10

### Work

Compute drawdown multiplier each backtest day.

### Acceptance Criteria

- Multiplier stored in hybrid state.
- Missing reflection/hybrid mode does not affect baseline.

## Task 14.2 — Apply Drawdown Multiplier in Risk Manager

**Type:** Code  
**Files:** `src/agents/risk_manager.py`  
**Depends on:** Task 14.1

### Work

Multiply existing risk limit by drawdown multiplier.

### Acceptance Criteria

- Near floor reduces exposure.
- At floor blocks new risky exposure.

## Task 14.3 — Add Fractional Kelly Helper

**Type:** Code  
**Files:** `src/risk/sizing.py`  
**Depends on:** Phase 2

### Work

Implement capped fractional Kelly estimate.

### Acceptance Criteria

- Disabled by default.
- Output is capped.
- Bad inputs return zero or safe default.

## Task 14.4 — Add Optional Kelly Sizing Hint to Risk Reasoning

**Type:** Code  
**Files:** `src/agents/risk_manager.py`  
**Depends on:** Task 14.3

### Work

Expose Kelly hint in reasoning only, not authoritative sizing initially.

### Acceptance Criteria

- Does not increase exposure by default.
- Helps future diagnostics.

## Task 14.5 — Add Drawdown and Sizing Tests

**Type:** Test  
**Files:** `tests/test_hybrid_sizing.py`  
**Depends on:** Tasks 14.1–14.4

### Work

Test floor and Kelly edge cases.

### Acceptance Criteria

- No leverage explosion.
- No division-by-zero crash.

---

# Phase 15: Post-MVP Reflection Evaluation

## Task 15.1 — Add Reflection Log Reader

**Type:** Code  
**Files:** `src/reflection/evaluator.py`  
**Depends on:** Phase 10

### Work

Read JSONL reflection records.

### Acceptance Criteria

- Handles malformed lines gracefully.

## Task 15.2 — Add Outcome Annotation Tool

**Type:** Code  
**Files:** `src/reflection/evaluator.py`  
**Depends on:** Task 15.1

### Work

Add post-hoc annotation for:

- 1d return
- 5d return
- 20d return
- max drawdown after trade

### Acceptance Criteria

- Does not run during same-day decision generation.
- Clearly separated post-processing step.

## Task 15.3 — Add Agent Contribution Report

**Type:** Code  
**Files:** `src/reflection/evaluator.py` or `scripts/reflection_report.py`  
**Depends on:** Task 15.2

### Work

Compute per-agent contribution metrics.

### Acceptance Criteria

- Reports agents associated with winning/losing decisions.
- Handles sparse data.

## Task 15.4 — Add Confidence Calibration Report

**Type:** Code  
**Files:** `src/reflection/evaluator.py` or `scripts/reflection_report.py`  
**Depends on:** Task 15.2

### Work

Bucket predictions by confidence and compare to realized directional accuracy.

### Acceptance Criteria

- Produces calibration table.
- Does not claim statistical validity with tiny samples.

## Task 15.5 — Add Suppressed Trade Outcome Report

**Type:** Code  
**Files:** `src/reflection/evaluator.py` or `scripts/reflection_report.py`  
**Depends on:** Task 15.2

### Work

Evaluate whether suppressed trades would have helped or hurt.

### Acceptance Criteria

- Report separates avoided losses from missed gains.

---

# Phase 16: Post-MVP UI/API Exposure

## Task 16.1 — Add Hybrid Fields to Backend Response Models

**Type:** Code  
**Files:** `app/backend/**`  
**Depends on:** MVP

### Work

Expose hybrid trace in API response when present.

### Acceptance Criteria

- Existing frontend consumers do not break.
- Hybrid field is optional.

## Task 16.2 — Add Hybrid Trace Panel to Frontend

**Type:** Code  
**Files:** `app/frontend/**`  
**Depends on:** Task 16.1

### Work

Display:

- consensus
- guardrail score
- meta-label
- risk multiplier
- selected agents

### Acceptance Criteria

- Hidden if hybrid data absent.
- Does not clutter baseline view.

## Task 16.3 — Add Debate Visualization

**Type:** Code  
**Files:** `app/frontend/**`  
**Depends on:** Phase 13 and Task 16.2

### Work

Show bull case, bear case, and red-team critique.

### Acceptance Criteria

- Clear distinction between thesis and final trade.

## Task 16.4 — Add Agent Graph Visualization

**Type:** Code  
**Files:** `app/frontend/**`  
**Depends on:** Phase 12

### Work

Show selected agents and edges in adaptive GoA mode.

### Acceptance Criteria

- Graph appears only when GoA mode is active.

## Task 16.5 — Add Reflection Report UI

**Type:** Code  
**Files:** `app/frontend/**`, `app/backend/**`  
**Depends on:** Phase 15

### Work

Expose reflection reports in web UI.

### Acceptance Criteria

- User can inspect agent attribution and calibration summaries.

---

# Phase 17: Post-MVP Advanced Allocation Research

## Task 17.1 — Add Allocation Interface

**Type:** Code  
**Files:** `src/portfolio/allocators/base.py`  
**Depends on:** MVP

### Work

Define common allocator interface.

### Acceptance Criteria

- Existing portfolio manager does not depend on it yet.

## Task 17.2 — Add Simple Signal-Weighted Allocator

**Type:** Code  
**Files:** `src/portfolio/allocators/signal_weighted.py`  
**Depends on:** Task 17.1

### Work

Create deterministic allocator using calibrated confidence and volatility.

### Acceptance Criteria

- Output weights are bounded.
- No optimizer required.

## Task 17.3 — Add HRP Research Stub

**Type:** Code / Research  
**Files:** `src/portfolio/allocators/hrp.py`  
**Depends on:** Task 17.1

### Work

Create placeholder or minimal implementation for hierarchical risk parity.

### Acceptance Criteria

- Clearly marked experimental.
- Disabled by default.

## Task 17.4 — Add Black-Litterman Research Stub

**Type:** Code / Research  
**Files:** `src/portfolio/allocators/black_litterman.py`  
**Depends on:** Task 17.1

### Work

Create interface-level placeholder for future Agentic Black-Litterman.

### Acceptance Criteria

- No production dependency.
- Disabled by default.

## Task 17.5 — Add Advanced Allocation Documentation

**Type:** Documentation  
**Files:** `docs/hybrid-decision-engine/advanced-allocation.md`  
**Depends on:** Tasks 17.1–17.4

### Work

Explain experimental allocation modules and limitations.

### Acceptance Criteria

- Clear warning that these are research features.

---

# Phase 18: Release, Maintenance, and Evaluation

## Task 18.1 — Add Hybrid Mode Changelog Entry

**Type:** Documentation  
**Files:** `CHANGELOG.md` or docs changelog  
**Depends on:** MVP

### Work

Summarize new hybrid functionality.

### Acceptance Criteria

- MVP features listed.
- Known limitations listed.

## Task 18.2 — Add Known Limitations Document

**Type:** Documentation  
**Files:** `docs/hybrid-decision-engine/known-limitations.md`  
**Depends on:** MVP

### Work

Document limitations:

- not investment advice
- not live trading
- confidence is approximate
- calibration needs sample size
- backtests may overfit

### Acceptance Criteria

- Clear user-facing caveats.

## Task 18.3 — Add Future Research Backlog

**Type:** Documentation  
**Files:** `docs/hybrid-decision-engine/future-research.md`  
**Depends on:** MVP

### Work

List future ideas:

- full Safe Debate multi-round protocol
- richer base-rate library
- agent performance memory
- signal-aware HRP
- Agentic Black-Litterman
- UI graph visualization

### Acceptance Criteria

- Backlog is separated from MVP requirements.

## Task 18.4 — Add Final MVP Acceptance Review

**Type:** Review  
**Files:** None  
**Depends on:** Tasks 18.1–18.3

### Work

Verify:

- baseline still works
- hybrid basic works
- tests pass
- docs explain feature flags
- safety invariants preserved

### Acceptance Criteria

- MVP is ready to merge/release.

---

## 12. Dependency Summary

No task should require all future phases. The critical no-blocker path is:

```text
Schemas
  -> deterministic utilities
  -> hybrid state helpers
  -> guardrail agent
  -> consensus agent
  -> meta-labeler
  -> feature flags
  -> risk integration
  -> portfolio integration
  -> reflection recorder
  -> MVP validation
```

Post-MVP phases are independently expandable:

```text
Adaptive GoA
Safe Debate Full
Drawdown/Sizing Enhancements
Reflection Evaluation
UI/API Exposure
Advanced Allocation Research
```

## 13. MVP Definition of Done

The MVP is done when:

- Hybrid mode can be enabled from CLI/backtester.
- Consensus, guardrail, and meta-label outputs are generated.
- Risk manager applies hybrid multipliers.
- Portfolio manager respects suppress/reduce/hold-only labels.
- Reflection recorder can write JSONL decision traces.
- Baseline mode still works unchanged.
- Unit and integration tests pass.
- Documentation explains how to use and validate the feature.

## 14. Post-MVP Definition of Done

Post-MVP is done when:

- Adaptive GoA selection runs and records selected agents.
- Full Safe Debate produces bull, bear, and red-team traces.
- Reflection evaluator reports calibration, attribution, and suppression outcomes.
- UI/API exposes hybrid decision traces.
- Advanced allocation modules remain optional and disabled by default.

## 15. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Hybrid layer breaks baseline flow | High | Feature flags default off; compatibility tests |
| LLM output bypasses constraints | High | Portfolio manager keeps deterministic allowed actions |
| Guardrails over-suppress useful trades | Medium | Reflection report tracks missed gains |
| Calibration claims overfit small samples | Medium | Report sample sizes and uncertainty |
| Complexity grows too quickly | High | Atomic tasks and MVP-first sequencing |
| Reflection leaks future data | High | Future return annotation only post-decision |

## 16. Implementation Guidance for AI Developer Agent

Start with the first vertical slice:

```text
Phase 1 -> Phase 2 -> Phase 3
```

Do not modify workflow topology until schemas, deterministic utilities, and state helpers exist.

First implementation PR should ideally include only:

```text
src/schemas/hybrid.py
src/risk/disagreement.py
src/risk/drawdown_guardrail.py
src/graph/hybrid_state.py
tests for the above
```

Then proceed to guardrail, consensus, and meta-label agents.

## 17. Final Product Principle

The app should become smarter because it becomes more skeptical, not because it lets more agents vote louder.

The final architecture should preserve this rule:

```text
LLMs argue.
Psychology audits.
Math sizes.
Risk vetoes.
Backtests remember.
```
