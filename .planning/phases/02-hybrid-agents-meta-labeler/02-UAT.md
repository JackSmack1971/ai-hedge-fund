---
status: complete
phase: 02-hybrid-agents-meta-labeler
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md]
started: 2026-06-09T00:00:00Z
updated: 2026-06-09T00:00:00Z
---

## Current Test

[testing complete]

## Tests

<!-- USER-FLOW SECTION -->

### 1. New agent tests pass
expected: Run `poetry run pytest tests/agents/test_psychological_guardrail.py tests/agents/test_consensus.py tests/agents/test_debate.py tests/agents/test_meta_labeler.py -v`. All 46 tests pass (16 guardrail/consensus + 30 debate/meta-labeler). No failures, no errors.
result: pass

### 2. Guardrail agent writes calibrated confidence
expected: With `hybrid_mode=True` in AgentState, `psychological_guardrail_agent` returns state with `data["guardrail_outputs"]` populated. Each ticker entry has a `confidence_multiplier` (between 0 and 1) and non-empty `reasoning` text. No LLM error, no missing keys.
result: pass

### 3. Consensus agent tallies analyst votes
expected: With `hybrid_mode=True` and multiple analyst signals in state, `consensus_agent` returns state with `data["consensus_output"]` populated. Each ticker entry has `dominant_stance` (bullish/bearish/neutral), a numeric `consensus_confidence`, and a `narrative_summary` string.
result: pass

### 4. Debate agent runs three LLM rounds
expected: With `hybrid_mode=True` and `debate_mode=True`, `debate_agent` returns state with `data["debate_outputs"]` populated. Each ticker entry has `bull_case`, `bear_case`, and `risk_red_team` fields — confirming all three sequential LLM calls (Bull/Bear/RedTeam) fired and returned structured output.
result: pass

### 5. Meta-labeler produces trade permission labels
expected: With populated `guardrail_outputs` and `debate_outputs` in state, `meta_labeler_agent` returns state with `data["meta_label_outputs"]` populated. Each ticker entry has `allow_trade` (bool), `size_multiplier` (0.0–1.0), and `label` (one of: suppress/hold_only/reduce/allow).
result: pass

<!-- TECHNICAL CHECKS -->

### 6. Hybrid mode off = no-op for all four agents
expected: With `hybrid_mode=False` in AgentState, all four agents (`psychological_guardrail_agent`, `consensus_agent`, `debate_agent`, `meta_labeler_agent`) return a state with `data={}` — no guardrail/consensus/debate/meta_label keys written, and no LLM calls made.
result: pass

### 7. Suppress label fires at low confidence
expected: When `calibrated_confidence < 30` for a ticker, `meta_labeler_agent` sets `label="suppress"`, `allow_trade=False`, and `size_multiplier=0.0` for that ticker. The threshold boundary at exactly 29 also triggers suppress (not hold_only).
result: pass

### 8. Priority rules: suppress beats other labels
expected: When a ticker meets both suppress conditions AND reduce conditions (3+ unresolved conflicts), the final label is `suppress` — not `reduce`. When it meets both suppress and hold_only conditions, the final label is also `suppress`. Confirm priority: suppress > hold_only > reduce > allow.
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
