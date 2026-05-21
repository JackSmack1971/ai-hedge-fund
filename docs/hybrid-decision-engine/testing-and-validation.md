# Testing and Validation Plan

## Purpose

The Hybrid Decision Engine introduces new reasoning layers. Testing must prove that these layers improve analysis without breaking deterministic portfolio safety.

The system must be tested as a research/backtesting engine, not a live trading product.

## 1. Safety Invariants

Every test suite must preserve these invariants:

1. LLM outputs never directly mutate portfolio state.
2. LLM outputs never bypass allowed actions.
3. LLM outputs never exceed max quantity.
4. Missing hybrid metadata preserves old behavior.
5. Suppressed or hold-only meta-labels force hold.
6. Drawdown floor breach prevents new risky exposure.
7. Backtest reflection never leaks future returns into the decision step.

## 2. Unit Tests

### 2.1 Hybrid Schemas

Test file suggestion:

```text
tests/test_hybrid_schemas.py
```

Required tests:

- valid regime classifications serialize to JSON
- invalid regime labels fail validation
- valid guardrail outputs serialize to JSON
- meta-label values are restricted to allowed labels
- hybrid trace can include optional `None` fields

### 2.2 Disagreement Scoring

Test file suggestion:

```text
tests/test_disagreement.py
```

Cases:

```text
all bullish high confidence -> low disagreement
half bullish half bearish -> high disagreement
all neutral -> low directional conviction
missing confidence -> handled safely
empty signals -> conservative default
```

### 2.3 Confidence Multiplier

Cases:

```text
high disagreement -> multiplier <= 0.50
moderate disagreement -> multiplier <= 0.75
high subjectivity -> multiplier reduced
multiplier never exceeds 1.0 in first version
multiplier never drops below configured floor unless suppression is explicit
```

### 2.4 Drawdown Guardrail

Test file suggestion:

```text
tests/test_drawdown_guardrail.py
```

Cases:

```text
portfolio above floor -> positive cushion
portfolio near floor -> reduced multiplier
portfolio below floor -> multiplier = 0.0
TIPP mode ratchets floor after new high if enabled
```

### 2.5 Meta-Labeler

Cases:

```text
low calibrated confidence -> suppress
high disagreement + high volatility -> hold_only
moderate confidence -> reduce
strong clean signal -> allow
size_multiplier bounded 0.0 to 1.0
```

## 3. Integration Tests

### 3.1 Existing Behavior Compatibility

Run baseline commands with hybrid features disabled.

Expected:

- same result keys exist
- no required hybrid metadata
- risk manager does not error when `state["data"].get("hybrid")` is missing
- portfolio manager does not error when meta-labels are missing

### 3.2 Guardrail-to-Risk Integration

Construct a fake state with:

```text
high disagreement
meta_label = reduce
confidence_multiplier = 0.50
size_multiplier = 0.50
```

Expected:

- risk manager applies multipliers
- remaining position limit is lower than baseline
- risk reasoning includes applied multipliers

### 3.3 Suppression-to-Portfolio Integration

Construct a fake state with:

```text
meta_label = suppress
```

Expected:

- allowed actions for ticker become `{"hold": 0}`
- final decision cannot buy/sell/short/cover
- LLM failure or malicious output still results in hold/default-safe behavior

### 3.4 Reflection Recorder

Expected:

- backtest step creates JSONL record when enabled
- record contains date, ticker, selected agents, final decision, and portfolio value
- future return fields are absent or null during decision step

## 4. Backtest Evaluation

Run comparative backtests:

```text
Baseline static mode
Hybrid guardrails only
Hybrid guardrails + meta-labeler
Hybrid full GoA + debate + reflection
```

Track:

- CAGR
- Sharpe ratio
- Sortino ratio
- max drawdown
- turnover
- number of suppressed trades
- average confidence before/after guardrails
- trade hit rate
- average realized return of suppressed trades
- agent contribution by regime

## 5. Calibration Metrics

Initial implementation may use approximate calibration.

Recommended metrics:

```text
Expected Calibration Error proxy
Brier score for directional predictions
confidence bucket accuracy
suppressed trade opportunity cost
false-positive reduction
```

Confidence bucket example:

```text
0-20% confidence -> observed hit rate
20-40% confidence -> observed hit rate
40-60% confidence -> observed hit rate
60-80% confidence -> observed hit rate
80-100% confidence -> observed hit rate
```

A well-calibrated system should not show 80-100% confidence buckets with low hit rates over repeated tests.

## 6. Regression Expectations

Hybrid mode does not need to improve CAGR immediately.

It should first improve:

- lower max drawdown
- lower turnover
- fewer high-confidence wrong trades
- fewer trades during high-disagreement regimes
- clearer reasoning trace
- better auditability

## 7. Failure Conditions

A pull request should fail review if:

- LLM output can directly mutate portfolio state
- portfolio manager accepts unconstrained quantities
- suppressed trades can still execute
- hybrid mode breaks baseline mode
- tests require network access unnecessarily
- future outcome data leaks into same-day decisions
- reflection automatically rewrites prompts or agent behavior without explicit user control

## 8. Manual Review Checklist

Before merging hybrid changes, verify:

- new modules are feature-flagged
- schemas are documented
- state shape is backward compatible
- progress display still works
- CLI/backtester still run
- web backend is not broken by missing hybrid metadata
- all risk/portfolio changes fail closed
