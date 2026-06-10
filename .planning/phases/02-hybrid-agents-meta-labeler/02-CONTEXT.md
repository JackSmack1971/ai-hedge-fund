# Phase 2: Hybrid Agents & Meta-Labeler - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Implements the four LLM-backed hybrid agents that run after the analyst layer:
psychological_guardrail_agent (PSY-01), consensus_agent (DEBT-01), the Safe Debate
layer (DEBT-02), and meta_labeler_agent (META-01). All four agents are gated — they
are no-ops unless `state["data"]["hybrid_mode"]` is True. The deterministic math from
Phase 1 (`src/risk/`) is called from the guardrail agent.

This phase does NOT wire these agents into the LangGraph workflow (that is Phase 3).
It delivers standalone, testable agent functions that read from and write to
`state["data"]`.

</domain>

<decisions>
## Implementation Decisions (from Phase 1 CONTEXT.md + new Phase 2 constraints)

### Existing Locked Decisions (Phase 1)
- D-01 through D-15 from 01-CONTEXT.md remain in effect.

### New Phase 2 Decisions

- **D-16 (Hybrid Mode Gate):** Every Phase 2 agent checks `state["data"].get("hybrid_mode", False)`.
  If False, the agent is a no-op (returns empty message + unmodified data). This preserves
  baseline behavior when hybrid features are not enabled.

- **D-17 (Output Keys):** Phase 2 agents write to dedicated top-level keys in `state["data"]`:
  - `guardrail_outputs` — dict keyed by ticker → `GuardrailOutput.model_dump()`
  - `consensus_output` — dict keyed by ticker → `ConsensusReport.model_dump()`
  - `debate_outputs` — dict keyed by ticker → `DebateOutput.model_dump()` or None
  - `meta_label_outputs` — dict keyed by ticker → `MetaLabelOutput.model_dump()`

- **D-18 (Debate Mode Sub-Gate):** Safe Debate additionally checks
  `state["data"].get("debate_mode", False)`. If False, debate_outputs stores None per ticker.

- **D-19 (Stance Extraction):** Only analyst agents (not risk_management_agent, portfolio_manager)
  contribute stances. Analyst signals with no ticker key are skipped. Stances: bullish=+1,
  neutral=0, bearish=-1.

- **D-20 (Herding Threshold):** herding_flag = True when disagreement_score < 0.15 AND
  n_analysts >= 3 AND all analysts agree (|sum(stances)| == n_analysts).

- **D-21 (Overconfidence Threshold):** overconfidence_flag = True when raw_confidence > 80
  AND disagreement_score < 0.2.

- **D-22 (Subjectivity):** Subjectivity score = fraction of selected analysts that are
  sentiment-type ("news_sentiment_analyst", "sentiment_analyst"). Penalty applied if > 0.3.

- **D-23 (Meta-Label Rules - Deterministic):**
  - calibrated_confidence < 30 OR confidence_multiplier < 0.40 → "suppress" (allow_trade=False, size_multiplier=0.0)
  - calibrated_confidence < 50 OR confidence_multiplier < 0.60 → "hold_only" (allow_trade=True, size_multiplier=0.5)
  - n_unresolved_conflicts >= 3 → "reduce" (allow_trade=True, size_multiplier=0.7)
  - otherwise → "allow" (allow_trade=True, size_multiplier=confidence_multiplier)
  Rules are evaluated in this priority order (suppress > hold_only > reduce > allow).

- **D-24 (Debate Agents):** Three sequential LLM calls per ticker: BullResearcher prompt →
  BearResearcher prompt → RiskRedTeam prompt. Each call is independent. The Red Team sees
  both bull_case and bear_case in its prompt.

- **D-25 (ConsensusReport inline schema):** Define `ConsensusReport` as a module-level
  Pydantic model in `src/agents/consensus.py` (not in hybrid.py, since it's agent-internal).

### the agent's Discretion
- The agent is free to choose prompt wording, test data setup, and helper names.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before implementing.**

### Planning Files
- [PROJECT.md](file:///c:/workspaces/ai-hedge-fund-forked/.planning/PROJECT.md)
- [REQUIREMENTS.md](file:///c:/workspaces/ai-hedge-fund-forked/.planning/REQUIREMENTS.md)
- [ROADMAP.md](file:///c:/workspaces/ai-hedge-fund-forked/.planning/ROADMAP.md)
- [Phase 1 CONTEXT.md](file:///c:/workspaces/ai-hedge-fund-forked/.planning/phases/01-foundation-schemas/01-CONTEXT.md)

### Codebase Files
- [hybrid.py](file:///c:/workspaces/ai-hedge-fund-forked/src/schemas/hybrid.py) — Output schemas (GuardrailOutput, DebateOutput, MetaLabelOutput)
- [disagreement.py](file:///c:/workspaces/ai-hedge-fund-forked/src/risk/disagreement.py) — compute_disagreement_score, compute_disagreement_multiplier
- [state.py](file:///c:/workspaces/ai-hedge-fund-forked/src/graph/state.py) — AgentState
- [llm.py](file:///c:/workspaces/ai-hedge-fund-forked/src/utils/llm.py) — call_llm helper
- [warren_buffett.py](file:///c:/workspaces/ai-hedge-fund-forked/src/agents/warren_buffett.py) — Agent pattern reference
- [tests/agents/conftest.py](file:///c:/workspaces/ai-hedge-fund-forked/tests/agents/conftest.py) — Test fixture patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Agent Pattern
- Agent function receives `(state: AgentState, agent_id: str = "agent_name")`
- Iterates over `state["data"]["tickers"]`
- Calls `call_llm(prompt, pydantic_model, agent_name=agent_id, state=state)` for LLM
- Returns `{"messages": state["messages"] + [HumanMessage(...)], "data": updated_data}`
- Data merge is shallow: returning `{"data": {"new_key": ...}}` adds to existing data

### Analyst Signals Structure
```python
state["data"]["analyst_signals"] = {
    "warren_buffett_agent": {
        "AAPL": {"signal": "bullish", "confidence": 75, "reasoning": "..."},
    },
    "risk_management_agent": {  # NOT an analyst — skip in guardrail
        "AAPL": {"remaining_position_limit": 10000, ...},
    },
}
```

### Test Pattern
- Mock `call_llm` via patch
- Build minimal state dict with `_make_empty_state()` from conftest
- Assert on `state["data"]` keys written by the agent

</code_context>

<specifics>
## Specific Implementation Notes

**No hybrid_mode gate needed in tests** — tests explicitly set `state["data"]["hybrid_mode"] = True`.

**Consensus agent:** For each ticker, count bullish/bearish/neutral votes from analyst signals.
Dominant = mode of stances. Call LLM to produce a narrative summary and list unresolved conflicts.

**Debate output when disabled:** store `None` per ticker in `debate_outputs` so downstream agents
can safely check `debate_outputs.get(ticker)` without KeyError.

</specifics>

<deferred>
## Deferred Ideas

- Weighting analyst signals by their historical accuracy — deferred to v2 (CAL-01).
- Structured LLM tool calling for debate agents — current simple prompt approach is sufficient.

</deferred>

---

*Phase: 2-Hybrid Agents & Meta-Labeler*
*Context gathered: 2026-06-09*
