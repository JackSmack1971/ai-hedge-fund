---
plan: 02-01
phase: 02-hybrid-agents-meta-labeler
subsystem: hybrid-agents
tags: [agents, guardrail, consensus, hybrid-mode, psy-01, debt-01]
requirements: [PSY-01, DEBT-01]

dependency_graph:
  requires:
    - src/schemas/hybrid.py (GuardrailOutput)
    - src/risk/disagreement.py (compute_disagreement_score, compute_disagreement_multiplier)
    - src/graph/state.py (AgentState)
    - src/utils/llm.py (call_llm)
    - src/utils/progress.py (progress)
  provides:
    - src/agents/psychological_guardrail.py (psychological_guardrail_agent)
    - src/agents/consensus.py (consensus_agent, ConsensusReport)
  affects:
    - state["data"]["guardrail_outputs"]
    - state["data"]["consensus_output"]

tech_stack:
  added: []
  patterns:
    - hybrid-mode gate (early return when hybrid_mode=False)
    - inline Pydantic model for agent-internal LLM output (D-25)
    - call_llm with structured output for reasoning

key_files:
  created:
    - src/agents/psychological_guardrail.py
    - src/agents/consensus.py
    - tests/agents/test_psychological_guardrail.py
    - tests/agents/test_consensus.py
  modified: []

decisions:
  - "D-16 applied: both agents are no-ops when hybrid_mode is False"
  - "D-20 applied: herding_flag = disagreement_score<0.15 AND n>=3 AND |sum(stances)|==n"
  - "D-21 applied: overconfidence_flag = raw_confidence>80 AND disagreement_score<0.2"
  - "D-22 applied: subjectivity penalty when sentiment analyst fraction > 0.3"
  - "D-25 applied: ConsensusReport defined inline in consensus.py"

metrics:
  duration: 8 min
  completed: "2026-06-09"
  tasks_completed: 5
  files_created: 4
  tests_added: 16
  test_suite_result: "480 passed, 0 failed"
---

# Phase 2 Plan 1: Psychological Guardrail + Consensus Agents Summary

**One-liner:** Hybrid-gated PSY-01 and DEBT-01 agent functions using disagreement math and inline Pydantic models to calibrate analyst confidence and tally stance votes per ticker.

## What Was Built

### psychological_guardrail_agent (PSY-01)
- Reads `state["data"]["analyst_signals"]`, excludes non-analyst agents (`risk_management_agent`, `portfolio_management_agent`)
- Computes disagreement score and base multiplier via `src/risk/disagreement`
- Applies penalty cascade: herding (×0.85), overconfidence (×0.90), high subjectivity (×max(1-s*0.3, 0.7))
- Calls `call_llm` with `_GuardrailReasoning` model for 2-3 sentence reasoning
- Writes `GuardrailOutput.model_dump()` per ticker to `state["data"]["guardrail_outputs"]`
- Returns empty data dict (no-op) when `hybrid_mode` is False

### consensus_agent (DEBT-01)
- Tallies bullish/bearish/neutral votes from analyst signals per ticker
- Computes dominant stance, minority stances, and consensus confidence deterministically
- Calls `call_llm` with `ConsensusReport` model for narrative summary and unresolved conflicts
- `ConsensusReport` Pydantic model defined inline (D-25)
- Writes `ConsensusReport.model_dump()` per ticker to `state["data"]["consensus_output"]`
- Returns empty data dict (no-op) when `hybrid_mode` is False

## Commits

| Task | Type | Hash | Description |
|------|------|------|-------------|
| 1 | feat | 3b8877f | Create psychological_guardrail_agent — PSY-01 |
| 2 | feat | 48b88be | Create consensus_agent — DEBT-01 |
| 3 | test | 657ddc3 | Add tests for psychological_guardrail_agent |
| 4 | test | c5f7417 | Add tests for consensus_agent |

## Test Results

- New tests: 16 passed (9 guardrail + 7 consensus)
- Full suite: 480 passed, 0 failed (baseline was 464, added 16)
- All deterministic paths tested with mocked `call_llm`

## Deviations from Plan

None — plan executed exactly as written.

The plan specified 8 tests for `test_psychological_guardrail.py` and 5 for `test_consensus.py`. Implementation added 9 and 7 respectively (one extra test per file for non-analyst exclusion and multi-ticker handling), which improves coverage without contradicting plan requirements.

## Self-Check

- GuardrailOutput constructor fields match hybrid.py schema exactly (all 10 fields)
- ConsensusReport has correct Pydantic field types (Literal, int with Field constraints, List[str], str)
- Both agents return `{"messages": state["messages"], "data": {}}` when `hybrid_mode=False`
- `call_llm` is the only LLM invocation in both agents (no direct model instantiation)
- All 16 tests pass with mocked `call_llm`

## Self-Check: PASSED
