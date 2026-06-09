# Phase 1: Foundation & Schemas - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Establishes the unified Pydantic data schemas for hybrid decision metadata and the core deterministic mathematical utilities (disagreement score, CPPI drawdown floor, and fractional Kelly helper). This phase does not change any agent execution logic or integrate the new metrics into the active risk/portfolio manager nodes, ensuring that the baseline trading behavior remains completely unchanged unless explicitly configured.

</domain>

<decisions>
## Implementation Decisions

### Stance Representation & Disagreement Metric
- **D-01:** Represent analyst recommendations numerically: Buy as +1, Hold/Neutral as 0, Sell as -1. This enables standard deviation and distance calculations.
- **D-02:** Calculate the disagreement score as the normalized standard deviation of stances across analysts, where maximum standard deviation represents a 50/50 split between Buy and Sell. The score is mapped to a risk sizing multiplier via linear decay: multiplier = 1.0 - disagreement_score.
- **D-03:** Handle missing or null analyst signals by imputing them as Hold/Neutral (0) in the standard deviation calculation, ensuring that all selected analysts are represented.

### CPPI Drawdown Floor
- **D-04:** Track the CPPI drawdown floor dynamically using a Trailing Peak Floor model: floor = Peak Value * (1 - max_drawdown_limit).
- **D-05:** Calculate the CPPI risk multiplier using Linear Cushion Scaling: multiplier = Cushion / (Max Drawdown Limit * Peak Value), capped at 1.0. The multiplier scales down allowed position limits as current portfolio value approaches the floor.
- **D-06:** Keep the max drawdown limit configurable via state data (e.g. state['data']['max_drawdown_limit']), with a fallback default of 0.20 (20%).
- **D-07:** Persist the peak portfolio value dynamically in the portfolio state (state['data']['portfolio']['peak_value']) across execution steps.

### Kelly Sizing
- **D-08:** Pass win_probability (p) and win_loss_ratio (b) explicitly as parameters to the Kelly helper function, letting the caller agent handle state lookup and logic.
- **D-09:** Scale the computed Kelly bet size to Quarter Kelly (0.25 multiplier) and enforce a strict cap of 25% of total portfolio value.
- **D-10:** Keep the Kelly sizing helper disabled by default via an enabled: bool = False argument in the function signature, returning a neutral 1.0 multiplier when disabled.
- **D-11:** Floor the resulting Kelly allocation at 0.0 (no negative values or short position triggers from the Kelly calculation itself).

### Pydantic Schema Extensibility
- **D-12:** Ignore and drop extra JSON fields silently when parsing model inputs, avoiding validation errors for unexpected LLM output fields.
- **D-13:** Define HybridDecisionTrace as a comprehensive schema containing ticker, timestamp, regime (RegimeClassification), selected analysts (list of IDs), debate (optional DebateOutput), guardrails (GuardrailOutput), final decision (MetaLabelOutput), and a reasoning summary.
- **D-14:** Represent optional fields as nullable with default None (e.g. FieldType | None = None).
- **D-15:** Keep all JSON key casing as snake_case only, maintaining consistency with Python and CLI conventions.

### the agent's Discretion
- The agent is free to choose internal function naming and standard test setups, provided all constraints are met.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Planning Files
- [PROJECT.md](file:///c:/workspaces/ai-hedge-fund-forked/.planning/PROJECT.md) — Overall project context, goals, and active requirements
- [REQUIREMENTS.md](file:///c:/workspaces/ai-hedge-fund-forked/.planning/REQUIREMENTS.md) — Requirements SCHM-01, RISK-01, RISK-02, RISK-03
- [ROADMAP.md](file:///c:/workspaces/ai-hedge-fund-forked/.planning/ROADMAP.md) — Phase 1 goals and success criteria

### Codebase Files
- [state.py](file:///c:/workspaces/ai-hedge-fund-forked/src/graph/state.py) — Current AgentState definition
- [risk_manager.py](file:///c:/workspaces/ai-hedge-fund-forked/src/agents/risk_manager.py) — Target agent for future integration of risk multipliers

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- [state.py](file:///c:/workspaces/ai-hedge-fund-forked/src/graph/state.py): Use AgentState as a reference for where portfolio and metadata are stored.

### Established Patterns
- Deterministic gating inside risk/portfolio managers. Standard math functions should be pure, easily testable, and have zero dependencies on LLMs.

### Integration Points
- New files to create: `src/schemas/hybrid.py`, `src/risk/disagreement.py`, `src/risk/drawdown_guardrail.py`, `src/risk/sizing.py`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Foundation & Schemas*
*Context gathered: 2026-06-09*
