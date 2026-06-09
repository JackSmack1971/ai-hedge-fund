---
phase: 02-hybrid-agents-meta-labeler
reviewed: 2026-06-09T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - src/agents/consensus.py
  - src/agents/debate.py
  - src/agents/meta_labeler.py
  - src/agents/psychological_guardrail.py
  - tests/agents/test_consensus.py
  - tests/agents/test_debate.py
  - tests/agents/test_meta_labeler.py
  - tests/agents/test_psychological_guardrail.py
findings:
  critical: 2
  warning: 3
  info: 4
  total: 9
status: fixed
---

# Phase 02: Code Review Report

**Reviewed:** 2026-06-09T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Four new agent modules (`consensus`, `debate`, `meta_labeler`, `psychological_guardrail`) and their companion test suites were reviewed. The agents implement the hybrid decision engine pipeline. The logic and schema choices are sound in isolation, but all four agents share a systematic state-mutation bug that will corrupt the LangGraph message log in real execution. A secondary behavioral bug allows the LLM to silently override deterministically-computed consensus fields. Several test weaknesses allow the bugs to go undetected in the current suite.

---

## Critical Issues

### CR-01: All four agents duplicate the entire message log on every invocation

**File:** `src/agents/consensus.py:104`, `src/agents/debate.py:115`, `src/agents/meta_labeler.py:105`, `src/agents/psychological_guardrail.py:145`

**Issue:** `AgentState.messages` is declared with `operator.add` as its LangGraph reducer. This means when a node returns a partial state update `{"messages": X}`, LangGraph does `operator.add(current_messages, X)`. All four agents return `{"messages": state["messages"] + [message]}` — that is, the full existing message list plus the new entry. The reducer then appends this entire list to the current state, doubling every prior message plus adding the new one. For a graph with N prior messages, each of these agents produces 2N+1 messages instead of N+1.

The established correct pattern throughout the rest of the codebase (12 other analyst agents, e.g. `src/agents/warren_buffett.py:156`, `src/agents/ben_graham.py:125`) is `{"messages": [message]}` — returning only the new message for the reducer to append.

The same bug affects the no-op early-return paths in all four agents:
- `consensus.py:34`, `debate.py:39`, `meta_labeler.py:36`, `psychological_guardrail.py:33`
all return `{"messages": state["messages"], "data": {}}`, which will append all existing messages again even when the agent does nothing.

The tests do not catch this because the test harness starts with an empty `state["messages"] = []`, making `[] + [message]` indistinguishable from `[message]` under the reducer.

**Fix:** Return only the new message in the delta:

```python
# All four agents — active path
return {
    "messages": [message],
    "data": {"consensus_output": consensus_output},   # adapt key per agent
}

# All four agents — no-op path
return {"messages": [], "data": {}}
```

---

### CR-02: LLM return value silently overwrites deterministically-computed consensus fields

**File:** `src/agents/consensus.py:85-95`

**Issue:** The function deterministically computes `dominant_stance`, `dominant_count`, and `consensus_confidence` from vote tallies (lines 69-73). These are only passed as *hints* in the prompt. The LLM is asked to return a full `ConsensusReport` (line 91, `pydantic_model=ConsensusReport`), and the result is stored verbatim:

```python
consensus_output[ticker] = result.model_dump()   # line 95
```

The LLM can return any value for `dominant_stance`, `dominant_count`, and `consensus_confidence` it sees fit. Downstream agents (`meta_labeler_agent`, portfolio manager) that consume `consensus_output` will see whatever the LLM fabricated, not the vote-tally result. This breaks the "deterministic priority rules" design intent (D-23) and creates a non-deterministic, untestable data boundary.

**Fix:** Either (a) use a narrow `_ConsensusSummaryOnly` model for the LLM call with only the fields the LLM should provide (`unresolved_conflicts`, `summary`), then construct the full `ConsensusReport` with the deterministic values:

```python
class _ConsensusSummaryOnly(BaseModel):
    unresolved_conflicts: List[str]
    summary: str

result = call_llm(prompt=..., pydantic_model=_ConsensusSummaryOnly, ...)
consensus_output[ticker] = ConsensusReport(
    dominant_stance=dominant_stance,
    dominant_count=dominant_count,
    minority_stances=minority_stances,
    consensus_confidence=consensus_confidence,
    unresolved_conflicts=result.unresolved_conflicts,
    summary=result.summary,
).model_dump()
```

Or (b) document clearly that the LLM is authoritative and remove the pre-computation logic, accepting full non-determinism.

---

## Warnings

### WR-01: Silent tie-breaking in consensus dominant stance is order-dependent

**File:** `src/agents/consensus.py:69`

**Issue:** When two stances have equal vote counts, `max(votes, key=lambda k: votes[k])` breaks the tie using Python dict insertion order. The `votes` dict is always initialized `{"bullish": 0, "bearish": 0, "neutral": 0}`, so a 1-bullish / 1-bearish tie will always silently resolve to `"bullish"`. A 1-bearish / 1-neutral tie resolves to `"bearish"`. This is non-obvious and undocumented. A tie is genuinely ambiguous and should either resolve to `"neutral"` explicitly or be surfaced as a conflict.

```python
# Current (silent order-dependent tie-break):
dominant_stance = max(votes, key=lambda k: votes[k])

# Suggested (explicit tie-break to neutral):
max_count = max(votes.values())
leaders = [s for s, c in votes.items() if c == max_count]
dominant_stance = leaders[0] if len(leaders) == 1 else "neutral"
```

There is no test covering a tie scenario.

---

### WR-02: `import pytest` is unused in all four test files

**File:** `tests/agents/test_consensus.py:5`, `tests/agents/test_debate.py:5`, `tests/agents/test_meta_labeler.py:5`, `tests/agents/test_psychological_guardrail.py:5`

**Issue:** `pytest` is imported in all four test files but never used — no `pytest.mark.*`, `pytest.raises`, `pytest.fixture`, or `pytest.param` appear anywhere in these files. Flake8 reports this as F401 (unused import). While not CI-blocking per project convention, it adds noise and suggests copy-paste origin.

**Fix:** Remove the unused import from each test file.

---

### WR-03: `test_majority_bullish_sets_dominant_stance` does not test computation — it tests the mock

**File:** `tests/agents/test_consensus.py:53-65`

**Issue:** The test patches `call_llm` with `_mock_consensus_report` which always returns `dominant_count=2`. The assertion `assert output["dominant_count"] == 2` then passes not because the agent computed `dominant_count=2`, but because the mock returned it. The actual computed `dominant_count` is lost in `consensus_output[ticker] = result.model_dump()` (CR-02 above). If CR-02 is fixed (only LLM-generated fields stored from mock), this test would then correctly validate the computation.

Until CR-02 is fixed, the test creates false confidence in the vote-tally computation. The correct approach is to test the deterministic fields against the pre-LLM computed values, not the mocked LLM output.

**Fix:** After fixing CR-02, the assertion `output["dominant_count"] == 2` will be testing the actual computed value. No code change needed in the test itself once the production fix is in place — but reviewers should be aware this test currently validates mock behavior, not agent logic.

---

## Info

### IN-01: `dominant_count` in no-signal path is 0 but `votes` dict still has 0-count entries

**File:** `src/agents/consensus.py:58-67`

**Issue:** The fast-path for `total == 0` correctly returns `dominant_count=0` but the early return `continue` skips the LLM call. However, the `ConsensusReport` is constructed with `minority_stances=[]`. This is correct. No bug, but the comment "No analyst signals available" is used in both the early-return and is also the expected text in the test assertion at line 44 — consistency is fine.

---

### IN-02: `_NON_ANALYST_AGENTS` is defined independently in both `consensus.py` and `psychological_guardrail.py`

**File:** `src/agents/consensus.py:17`, `src/agents/psychological_guardrail.py:18`

**Issue:** The same `frozenset({"risk_management_agent", "portfolio_management_agent"})` is copy-pasted in two files. If a new non-analyst agent is added, both constants must be updated independently.

**Fix:** Centralize in a shared location such as `src/utils/analysts.py` or a new `src/agents/_constants.py` and import from there.

---

### IN-03: `debate_agent` does not exclude non-analyst agents when building context

**File:** `src/agents/debate.py:52-59`

**Issue:** The `psychological_guardrail_agent` and `consensus_agent` both explicitly skip `_NON_ANALYST_AGENTS` when processing `analyst_signals`. The `debate_agent` has no such filter (lines 52-59). Signals from `risk_management_agent` or `portfolio_management_agent` would be included in the Bull/Bear context if they happen to appear in `analyst_signals`. This is inconsistent with sibling agents' behavior.

**Fix:** Apply the same exclusion:
```python
from src.agents.consensus import _NON_ANALYST_AGENTS  # or shared constant

for analyst_key, signal_data in analyst_signals.items():
    if analyst_key in _NON_ANALYST_AGENTS:
        continue
    ...
```

---

### IN-04: `guardrail_outputs.get(ticker, {})` silently defaults to empty dict when guardrail not run

**File:** `src/agents/meta_labeler.py:46-48`

**Issue:** When `guardrail_outputs` is absent or does not contain the ticker, `meta_labeler_agent` silently uses `calibrated_confidence=50` and `confidence_multiplier=1.0` as defaults. This means if the pipeline runs with `hybrid_mode=True` but guardrail output is missing (e.g., due to an upstream error or ordering issue), the meta-labeler will produce an `allow` label with a 1.0 multiplier — effectively a permissive pass-through rather than a safe default. The fail-safe direction would be to emit `suppress` or `hold_only` when guardrail data is absent.

**Fix:** Either fail loudly (log a warning and set a conservative default label), or document that the permissive default is intentional:
```python
guardrail = guardrail_outputs.get(ticker)
if guardrail is None:
    # No guardrail data — use conservative defaults
    calibrated_confidence = 0
    confidence_multiplier = 0.0
else:
    calibrated_confidence = int(guardrail.get("calibrated_confidence", 50))
    confidence_multiplier = float(guardrail.get("confidence_multiplier", 1.0))
```

---

_Reviewed: 2026-06-09T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
