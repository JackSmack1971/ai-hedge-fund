---
phase: 02-hybrid-agents-meta-labeler
verified: 2026-06-09T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 2: Hybrid Agents & Meta-Labeler Verification Report

**Phase Goal:** Calibrated confidence, consensus aggregation, debate layer, and meta-label permissions.
**Verified:** 2026-06-09
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The psychological guardrail calibrates raw confidence based on dispersion and herding | VERIFIED | `src/agents/psychological_guardrail.py`: computes `compute_disagreement_score`, applies herding (×0.85), overconfidence (×0.90), subjectivity penalties; produces `GuardrailOutput` with `calibrated_confidence` per ticker |
| 2 | The consensus agent aggregates opposing stances into a structured output | VERIFIED | `src/agents/consensus.py`: tallies bullish/bearish/neutral votes, derives `dominant_stance`, `minority_stances`, `consensus_confidence`; calls `call_llm` with inline `ConsensusReport` Pydantic model |
| 3 | The debate layer runs sequential bull/bear/red-team agents under the `debate_mode` flag | VERIFIED | `src/agents/debate.py`: exactly 3 `call_llm` calls per ticker when `debate_mode=True`; stores `None` per ticker when `debate_mode=False`; confirmed by test `test_debate_mode_on_calls_llm_three_times_per_ticker` (call_count[0] == 3) |
| 4 | The meta-labeler assigns correct permission labels and sizing scalars | VERIFIED | `src/agents/meta_labeler.py`: priority chain suppress > hold_only > reduce > allow with thresholds matching D-23 exactly; all 8 label/priority boundary tests pass |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/agents/psychological_guardrail.py` | PSY-01 guardrail agent | VERIFIED | 148 lines, full implementation, `GuardrailOutput.model_dump()` per ticker |
| `src/agents/consensus.py` | DEBT-01 consensus agent | VERIFIED | 107 lines, inline `ConsensusReport` Pydantic model (D-25 applied) |
| `src/agents/debate.py` | DEBT-02 debate agent | VERIFIED | 118 lines, 3 sequential `call_llm` calls, `DebateOutput` schema used |
| `src/agents/meta_labeler.py` | META-01 meta-labeler | VERIFIED | 108 lines, deterministic D-23 rule chain, `MetaLabelOutput` schema used |
| `tests/agents/test_psychological_guardrail.py` | Unit tests PSY-01 | VERIFIED | 9 tests, all pass; covers no-signal defaults, hybrid-gate, herding, overconfidence, subjectivity, non-analyst exclusion |
| `tests/agents/test_consensus.py` | Unit tests DEBT-01 | VERIFIED | 7 tests, all pass; covers no-signal defaults, hybrid-gate, majority stance, multi-ticker, non-analyst exclusion |
| `tests/agents/test_debate.py` | Unit tests DEBT-02 | VERIFIED | 10 tests, all pass; covers hybrid-gate, debate_mode=False/True, 3 LLM calls per ticker, output fields |
| `tests/agents/test_meta_labeler.py` | Unit tests META-01 | VERIFIED | 20 tests, all pass; covers all 4 labels, boundary conditions, priority chain, output storage |
| `src/schemas/hybrid.py` | Schema dependency (Phase 1) | VERIFIED | `GuardrailOutput`, `DebateOutput`, `MetaLabelOutput` all present and used by phase 2 agents |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `psychological_guardrail.py` | `src/risk/disagreement.py` | `compute_disagreement_score`, `compute_disagreement_multiplier` | WIRED | Both functions imported and called on lines 73-74 |
| `psychological_guardrail.py` | `src/schemas/hybrid.py` | `GuardrailOutput` | WIRED | Imported line 13, instantiated and `.model_dump()` on lines 59-70 and 122-133 |
| `debate.py` | `src/schemas/hybrid.py` | `DebateOutput` | WIRED | Imported line 16, instantiated on lines 99-106 |
| `meta_labeler.py` | `src/schemas/hybrid.py` | `MetaLabelOutput` | WIRED | Imported line 15, instantiated on lines 90-95 |
| `meta_labeler.py` | `guardrail_outputs` state key | `data.get("guardrail_outputs", {})` | WIRED | Line 39; reads `calibrated_confidence` and `confidence_multiplier` per ticker |
| `meta_labeler.py` | `debate_outputs` state key | `data.get("debate_outputs", {})` | WIRED | Line 40; reads `unresolved_conflicts` count per ticker |
| All 4 agents | `hybrid_mode` gate | `data.get("hybrid_mode", False)` | WIRED | All 4 agents perform early-return when False; verified by dedicated test in each test file |

### Data-Flow Trace (Level 4)

These agents do not render UI — they are pure state-transformation functions. Level 4 data-flow applies to the deterministic computation paths:

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `psychological_guardrail.py` | `guardrail_outputs` | `analyst_signals` from state + `compute_disagreement_score` | Yes — real math applied to signal stances | FLOWING |
| `consensus.py` | `consensus_output` | Vote tally from `analyst_signals`, then `call_llm` for narrative | Yes — deterministic tally + mocked LLM in tests | FLOWING |
| `debate.py` | `debate_outputs` | 3 sequential `call_llm` calls per ticker | Yes — real call chain, mocked in tests | FLOWING |
| `meta_labeler.py` | `meta_label_outputs` | `guardrail_outputs` + `debate_outputs` from state, deterministic rules | Yes — pure rule application, no hardcoded empty returns | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 46 phase 2 tests pass | `pytest tests/agents/test_psychological_guardrail.py tests/agents/test_consensus.py tests/agents/test_debate.py tests/agents/test_meta_labeler.py --no-cov` | 46 passed, 0 failed, 1.84s | PASS |
| debate_agent makes exactly 3 LLM calls per ticker | `test_debate_mode_on_calls_llm_three_times_per_ticker` | call_count[0] == 3 asserted and passing | PASS |
| meta_labeler priority: suppress > hold_only > reduce > allow | `TestMetaLabelerPriority` (3 tests) | All 3 pass | PASS |
| hybrid_mode=False is a no-op on all agents | `test_hybrid_mode_off_is_noop` in each test file | 4/4 pass | PASS |

### Probe Execution

No probe scripts declared or found for this phase. Step 7c: SKIPPED (no `scripts/*/tests/probe-*.sh` found for phase 2).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PSY-01 | 02-01-PLAN.md | Implement `psychological_guardrail_agent` converting raw analyst signals into calibrated confidence, herding flags, and confidence multipliers | SATISFIED | `src/agents/psychological_guardrail.py` fully implements all specified behaviors; 9 tests pass |
| DEBT-01 | 02-01-PLAN.md | Implement `consensus_agent` summarizing dominant/minority reports, consensus confidence, and unresolved conflicts | SATISFIED | `src/agents/consensus.py` fully implements all specified behaviors; 7 tests pass |
| DEBT-02 | 02-02-PLAN.md | Implement Safe Debate layer (Bull Researcher, Bear Researcher, Risk Red-Team sequential LLM agents) enabled via `debate_mode` flag | SATISFIED | `src/agents/debate.py` implements all 3 sequential LLM calls per ticker; `debate_mode` sub-gate stores None when disabled; 10 tests pass |
| META-01 | 02-02-PLAN.md | Implement `meta_labeler_agent` mapping guardrail outputs to permission labels (`allow`, `reduce`, `suppress`, `hold_only`) and size multipliers | SATISFIED | `src/agents/meta_labeler.py` implements D-23 priority chain exactly; boundary tests and priority tests all pass; 20 tests pass |

**NOTE — REQUIREMENTS.md traceability table is stale:** The `Traceability` table in `.planning/REQUIREMENTS.md` maps PSY-01 to Phase 3, DEBT-01/DEBT-02 to Phase 4, and META-01 to Phase 5. However, ROADMAP.md authoritatively assigns all four requirements to Phase 2, and both PLAN files declare them. The implementations exist and satisfy the requirement specs verbatim. The traceability table requires an update (documentation debt, not a code gap).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers in any of the 4 agent files or 4 test files | 

### Human Verification Required

None. All phase 2 success criteria are programmatically verifiable and confirmed by the test suite.

### Gaps Summary

No gaps. All 4 success criteria from ROADMAP.md are met by real, substantive implementations with passing test coverage. The REQUIREMENTS.md traceability table is stale (shows different phase numbers) but this is a documentation inconsistency — the actual roadmap contract and plan frontmatter are internally consistent and the implementations satisfy all requirement specs.

---

_Verified: 2026-06-09T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
