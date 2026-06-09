# Phase 3: Sizing & Execution Integrations - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrates the hybrid engine outputs produced in Phase 2 into the two deterministic execution
agents: `risk_manager.py` (INT-01) and `portfolio_manager.py` (INT-02). Also wires all four
hybrid agents (guardrail, consensus, debate, meta_labeler) into the LangGraph DAG via a single
composite `hybrid_layer` node, enabling the end-to-end flow to run with `hybrid_mode=True`.

This phase does NOT implement CPPI drawdown multiplier application (deferred to Phase 4) and does
NOT implement regime classification or adaptive routing (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### Risk Manager — Hybrid Multiplier Chaining (INT-01)

- **D-26 (Multiplier Chaining):** Multiplicative product — the hybrid-adjusted position limit is:
  `position_limit = total_portfolio_value × vol_multiplier × corr_multiplier × disagreement_multiplier × meta_size_multiplier`
  All four factors are multiplied together. Each independently shrinks the ceiling.

- **D-27 (Disagreement Source):** Read `guardrail_outputs[ticker]["confidence_multiplier"]` as the
  disagreement-derived multiplier (already computed by the guardrail agent from `src/risk/disagreement.py`).
  Do NOT call `compute_disagreement_score` again in risk_manager — reuse the guardrail output.

- **D-28 (Meta-Label Size in Risk Manager):** Read `meta_label_outputs[ticker]["size_multiplier"]`
  and apply it as an additional factor to `position_limit` (before subtracting current position value).

- **D-29 (CPPI Deferred):** CPPI drawdown multiplier (RISK-02 / `src/risk/drawdown_guardrail.py`) is
  NOT applied in Phase 3. Portfolio has no floor tracking yet. Applied in Phase 4.

- **D-30 (Apply Point):** Hybrid multipliers are applied to `position_limit` (the ceiling), before
  `remaining_position_limit = position_limit - current_position_value` is computed.

- **D-31 (Hybrid Mode Gate):** If `hybrid_mode` is False, skip all hybrid multipliers → behavior
  unchanged from the baseline. If `guardrail_outputs` or `meta_label_outputs` are missing for a
  ticker, use neutral multipliers (1.0) — no-op, does not punish missing data.

### Portfolio Manager — Meta-Label Suppression (INT-02)

- **D-32 (suppress behavior):** When `meta_label == "suppress"` (allow_trade=False), force hold
  for that ticker: replace all allowed actions with `{"hold": 0}`. No buy, sell, short, or cover.
  This is the hard suppression of allow_trade=False.

- **D-33 (hold_only behavior):** When `meta_label == "hold_only"`, allow exits only: keep sell and
  cover in the allowed actions dict, but remove buy and short. Allows reducing risk but not adding.

- **D-34 (reduce behavior):** When `meta_label == "reduce"`, scale `max_shares[ticker]` by
  `size_multiplier` (0.7) before calling `compute_allowed_actions`. Integer floor truncation.

- **D-35 (allow behavior):** When `meta_label == "allow"`, scale `max_shares[ticker]` by
  `size_multiplier` (which equals `confidence_multiplier` from the guardrail). Same mechanism as
  reduce, just with a different multiplier value.

- **D-36 (Injection Point):** Meta-label filtering is injected inside `portfolio_management_agent`,
  after `max_shares` is computed per ticker, before `generate_trading_decision` is called.

- **D-37 (Hybrid Gate in PM):** If `hybrid_mode` is False or `meta_label_outputs` is missing,
  skip all meta-label filtering — behavior unchanged.

### LangGraph Wiring

- **D-38 (Single Composite Node):** All four hybrid agents (guardrail, consensus, debate,
  meta_labeler) are bundled into a single `hybrid_layer` node in the graph. The node function calls
  them sequentially: guardrail → consensus → debate → meta_labeler. This avoids 4 graph node
  additions while keeping agent functions individually testable.

- **D-39 (DAG Placement):** The `hybrid_layer` node runs after all analyst agents converge,
  before `risk_management_agent`:
  `[analysts in parallel] → hybrid_layer → risk_management_agent → portfolio_manager`

- **D-40 (Always in Graph):** The hybrid_layer node is always added to the graph. When
  `hybrid_mode=False`, each agent function returns early as a no-op (D-16 from Phase 2).
  No conditional graph building.

### Claude's Discretion
- Exact helper function names and test data setup are at Claude's discretion.
- Whether `hybrid_layer` is implemented as a module-level function or inline lambda is at Claude's discretion.

</decisions>

<code_context>
## Existing Code Insights

### Risk Manager Existing Flow
- Calculates `vol_adjusted_limit_pct` via `calculate_volatility_adjusted_limit()`
- Calculates `corr_multiplier` via `calculate_correlation_multiplier()`
- `combined_limit_pct = vol_adjusted_limit_pct × corr_multiplier`
- `position_limit = total_portfolio_value × combined_limit_pct`
- `remaining_position_limit = position_limit - current_position_value`
- `max_position_size = min(remaining_position_limit, portfolio["cash"])`

### Portfolio Manager Existing Flow
- Computes `max_shares[ticker]` from risk_manager output
- Calls `compute_allowed_actions(tickers, current_prices, max_shares, portfolio)`
- Sends to `generate_trading_decision(...)` with `allowed_actions`
- `compute_allowed_actions` is a standalone pure function (easy to unit test with meta-label scaling)

### Hybrid Agent Outputs (D-17)
- `state["data"]["guardrail_outputs"]` — dict keyed by ticker → GuardrailOutput.model_dump()
  - Key field: `confidence_multiplier` (float, 0.0-1.0)
- `state["data"]["meta_label_outputs"]` — dict keyed by ticker → MetaLabelOutput.model_dump()
  - Key fields: `allow_trade` (bool), `size_multiplier` (float), `label` (str)

### LangGraph DAG (src/main.py)
- `create_workflow()` builds a StateGraph with START → start_node → [analysts] → risk_management_agent → portfolio_manager → END
- Analyst nodes added via `get_analyst_nodes()` from `src/utils/analysts.py`
- Adding a new sequential node: `workflow.add_node("hybrid_layer", hybrid_layer_node)` + edges

### Existing Agents (Phase 2)
- `src/agents/psychological_guardrail.py` — `psychological_guardrail_agent`
- `src/agents/consensus.py` — `consensus_agent`
- `src/agents/debate.py` — `debate_agent`
- `src/agents/meta_labeler.py` — `meta_labeler_agent`

</code_context>

<specifics>
## Specific Implementation Notes

**CPPI explicitly deferred:** Do not call `src/risk/drawdown_guardrail.py` from risk_manager in
Phase 3. The function will be used in Phase 4.

**GuardrailOutput.confidence_multiplier as the disagreement multiplier:** The guardrail already
incorporates the disagreement score into its confidence_multiplier. Risk manager reads this directly
rather than re-computing disagreement from scratch.

**suppress vs hold_only distinction:** suppress (allow_trade=False) = no trades at all.
hold_only (allow_trade=True, size=0.5) = exits allowed. This creates a meaningful hierarchy.

**Main.py wiring location:** The `hybrid_layer` node must be wired between the last analyst edge
and the `risk_management_agent` node. The start_node fans out to analysts; currently all analysts
fan in to risk_management_agent. The new shape: analysts fan in to hybrid_layer, which then goes
to risk_management_agent.

</specifics>

<deferred>
## Deferred Ideas

- CPPI drawdown multiplier application in risk_manager — deferred to Phase 4 (no floor tracking).
- Separate graph nodes per hybrid agent (for fine-grained LangGraph visualization) — bundled into one composite node for simplicity.
- Web app graph: the React Flow visualization of the hybrid_layer node (visual representation in the frontend) — deferred, not in scope for this phase.

</deferred>

---

*Phase: 3-Sizing & Execution Integrations*
*Context gathered: 2026-06-09*
