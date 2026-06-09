---
plan: 02-02
phase: 02-hybrid-agents-meta-labeler
subsystem: agents
tags: [debate, meta-labeler, hybrid-mode, llm-agents, DEBT-02, META-01]
dependency_graph:
  requires:
    - 01-01 (hybrid schemas — DebateOutput, MetaLabelOutput)
    - 01-02 (risk utilities — disagreement score)
  provides:
    - src/agents/debate.py — debate_agent (DEBT-02)
    - src/agents/meta_labeler.py — meta_labeler_agent (META-01)
  affects:
    - 02-03 (Phase 3 wiring — these agents will be inserted into the LangGraph DAG)
tech_stack:
  added: []
  patterns:
    - Pydantic-structured LLM output via call_llm helper
    - hybrid_mode gate pattern (no-op return when disabled)
    - debate_mode sub-gate pattern (None-per-ticker when disabled)
    - Priority rule chain: suppress > hold_only > reduce > allow
key_files:
  created:
    - src/agents/debate.py
    - src/agents/meta_labeler.py
    - tests/agents/test_debate.py
    - tests/agents/test_meta_labeler.py
  modified: []
decisions:
  - D-18 applied: debate_mode sub-gate stores None per ticker when debate_mode=False
  - D-23 applied: suppress/hold_only/reduce/allow thresholds match spec exactly
  - D-24 applied: three sequential LLM calls (Bull/Bear/RedTeam) per ticker
metrics:
  duration: "~10 minutes"
  completed: "2026-06-09"
  tasks_completed: 5
  files_created: 4
---

# Phase 2 Plan 02: Safe Debate + Meta-Labeler Agents Summary

## One-liner

debate_agent runs 3 sequential LLM calls (Bull/Bear/RedTeam) per ticker with a debate_mode sub-gate; meta_labeler_agent applies deterministic priority rules (suppress > hold_only > reduce > allow) from D-23 to produce trade permission labels.

## What Was Built

### Task 1: `src/agents/debate.py` (DEBT-02)

Implements `debate_agent` with:
- `hybrid_mode` gate: returns empty data dict when hybrid_mode=False
- `debate_mode` sub-gate: stores `None` per ticker when debate_mode=False (no LLM calls)
- Three sequential `call_llm` calls per ticker when debate_mode=True:
  1. BullResearcher (`_BullCase` schema) — strongest bullish argument
  2. BearResearcher (`_BearCase` schema) — strongest bearish argument
  3. RiskRedTeam (`_RedTeam` schema) — attacks both cases, lists conflicts, provides debate_confidence
- Analyst signals from `state["data"]["analyst_signals"]` included as context in prompts
- Outputs `DebateOutput.model_dump()` per ticker to `state["data"]["debate_outputs"]`

### Task 2: `src/agents/meta_labeler.py` (META-01)

Implements `meta_labeler_agent` with:
- `hybrid_mode` gate: returns empty data dict when hybrid_mode=False
- Reads `guardrail_outputs` and `debate_outputs` from state
- Deterministic priority rules (D-23):
  - `suppress`: calibrated_confidence < 30 OR confidence_multiplier < 0.40 (allow_trade=False, size_multiplier=0.0)
  - `hold_only`: calibrated_confidence < 50 OR confidence_multiplier < 0.60 (allow_trade=True, size_multiplier=0.5)
  - `reduce`: n_unresolved_conflicts >= 3 (allow_trade=True, size_multiplier=0.7)
  - `allow`: all conditions pass (allow_trade=True, size_multiplier=confidence_multiplier)
- One LLM call per ticker (`_MetaReasoning`) for brief justification text
- Outputs `MetaLabelOutput.model_dump()` per ticker to `state["data"]["meta_label_outputs"]`

### Tasks 3+4: Tests

- `tests/agents/test_debate.py`: 10 tests across 4 test classes
  - TestDebateAgentHybridModeOff: no-op behavior, no LLM calls
  - TestDebateModeFalse: None-per-ticker storage, multi-ticker coverage
  - TestDebateModeTrue: 3 LLM calls per ticker, output fields, multi-ticker (6 calls total)
  - Message appended to state verification

- `tests/agents/test_meta_labeler.py`: 20 tests across 6 test classes
  - TestMetaLabelerHybridModeOff: no-op behavior
  - TestMetaLabelerSuppressLabel: confidence threshold, multiplier threshold, boundary at 29
  - TestMetaLabelerHoldOnlyLabel: medium confidence, medium multiplier, boundary at 30
  - TestMetaLabelerReduceLabel: 3+ conflicts, 5 conflicts, 2 conflicts (no-reduce)
  - TestMetaLabelerAllowLabel: all-good conditions, size_multiplier=confidence_multiplier
  - TestMetaLabelerPriority: suppress > reduce, suppress > hold_only, hold_only > reduce
  - TestMetaLabelerOutputStorage: field presence, message appended, default guardrail, None debate

### Task 5: Verification

All 30 new tests pass. Full suite: 464 passed, 0 failed (existing tests unaffected).

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. Both agents are fully wired to call_llm and produce real structured output.

## Threat Flags

No new network endpoints, auth paths, or trust boundary changes introduced. Both agents are internal state-passing functions.

## Self-Check: PASSED

Files created:
- src/agents/debate.py: EXISTS
- src/agents/meta_labeler.py: EXISTS
- tests/agents/test_debate.py: EXISTS
- tests/agents/test_meta_labeler.py: EXISTS

Commits:
- 3faaf6f: feat(02-02): implement debate_agent — DEBT-02
- b49dfd2: feat(02-02): implement meta_labeler_agent — META-01
- 11571ce: test(02-02): add tests for debate_agent and meta_labeler_agent

Test suite: 30/30 new tests passed, 464/464 existing tests passed.
