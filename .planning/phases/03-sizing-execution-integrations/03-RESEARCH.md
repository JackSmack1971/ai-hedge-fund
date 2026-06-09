# Phase 3: Sizing & Execution Integrations - Research

**Researched:** 2026-06-09
**Domain:** LangGraph agent integration — risk manager multiplier chaining, portfolio manager meta-label suppression, composite hybrid_layer DAG node
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Risk Manager — Hybrid Multiplier Chaining (INT-01)**

- **D-26 (Multiplier Chaining):** Multiplicative product — the hybrid-adjusted position limit is:
  `position_limit = total_portfolio_value × vol_multiplier × corr_multiplier × disagreement_multiplier × meta_size_multiplier`
  All four factors are multiplied together. Each independently shrinks the ceiling.

- **D-27 (Disagreement Source):** Read `guardrail_outputs[ticker]["confidence_multiplier"]` as the
  disagreement-derived multiplier. Do NOT call `compute_disagreement_score` again in risk_manager — reuse the guardrail output.

- **D-28 (Meta-Label Size in Risk Manager):** Read `meta_label_outputs[ticker]["size_multiplier"]`
  and apply it as an additional factor to `position_limit`.

- **D-29 (CPPI Deferred):** CPPI drawdown multiplier is NOT applied in Phase 3. Applied in Phase 4.

- **D-30 (Apply Point):** Hybrid multipliers are applied to `position_limit` (the ceiling), before
  `remaining_position_limit = position_limit - current_position_value` is computed.

- **D-31 (Hybrid Mode Gate):** If `hybrid_mode` is False, skip all hybrid multipliers. If
  `guardrail_outputs` or `meta_label_outputs` are missing for a ticker, use neutral multipliers (1.0).

**Portfolio Manager — Meta-Label Suppression (INT-02)**

- **D-32 (suppress behavior):** `meta_label == "suppress"` (allow_trade=False) → force hold for that
  ticker: replace all allowed actions with `{"hold": 0}`.

- **D-33 (hold_only behavior):** `meta_label == "hold_only"` → keep sell and cover in allowed actions,
  remove buy and short.

- **D-34 (reduce behavior):** `meta_label == "reduce"` → scale `max_shares[ticker]` by `size_multiplier`
  (0.7) before calling `compute_allowed_actions`. Integer floor truncation.

- **D-35 (allow behavior):** `meta_label == "allow"` → scale `max_shares[ticker]` by `size_multiplier`.

- **D-36 (Injection Point):** Meta-label filtering injected inside `portfolio_management_agent`, after
  `max_shares` is computed per ticker, before `generate_trading_decision` is called.

- **D-37 (Hybrid Gate in PM):** If `hybrid_mode` is False or `meta_label_outputs` is missing, skip
  all meta-label filtering.

**LangGraph Wiring**

- **D-38 (Single Composite Node):** All four hybrid agents (guardrail, consensus, debate, meta_labeler)
  bundled into a single `hybrid_layer` node. Sequential call order: guardrail → consensus → debate → meta_labeler.

- **D-39 (DAG Placement):** `[analysts in parallel] → hybrid_layer → risk_management_agent → portfolio_manager`

- **D-40 (Always in Graph):** hybrid_layer node always added. When `hybrid_mode=False`, each agent
  returns early as a no-op. No conditional graph building.

### Claude's Discretion

- Exact helper function names and test data setup are at Claude's discretion.
- Whether `hybrid_layer` is implemented as a module-level function or inline lambda is at Claude's discretion.

### Deferred Ideas (OUT OF SCOPE)

- CPPI drawdown multiplier application in risk_manager — deferred to Phase 4.
- Separate graph nodes per hybrid agent — bundled into one composite node.
- Web app graph: React Flow visualization of the hybrid_layer node — deferred.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INT-01 | Integrate risk_manager to consume hybrid guardrails, meta-label sizing multipliers, and drawdown multipliers to scale position limits | D-26 to D-31: exact apply point, multiplier chain, state key names, hybrid gate pattern all confirmed from codebase |
| INT-02 | Integrate portfolio_manager to enforce meta-label allowed actions (suppress/hold_only) and reduced quantities | D-32 to D-37: exact injection point, label semantics, compute_allowed_actions hook, hybrid gate pattern all confirmed from codebase |
</phase_requirements>

---

## Summary

Phase 3 integrates the hybrid engine outputs produced in Phase 2 into two deterministic execution agents (`risk_manager.py` for INT-01, `portfolio_manager.py` for INT-02) and wires all four hybrid agents into the LangGraph DAG via a new composite `hybrid_layer` node.

The changes are surgical: INT-01 is a ~15-line insertion in the inner loop of `risk_management_agent` that reads from `state["data"]["guardrail_outputs"]` and `state["data"]["meta_label_outputs"]`, multiplies two scalars into `position_limit`, and falls back to 1.0 when data is absent. INT-02 is a ~20-line insertion in `portfolio_management_agent` after `max_shares` is computed, dispatching on the `label` field of the meta-label output to filter or scale allowed actions. The LangGraph wiring change in `src/main.py::create_workflow` redirects all analyst fan-in edges from going directly to `risk_management_agent` to going through `hybrid_layer` instead.

The backend `app/backend/services/graph.py` creates its own `StateGraph` via `create_graph()` and does NOT call `run_hedge_fund` or `create_workflow` from `src/main.py`. Phase 3 wires the hybrid layer only in `src/main.py::create_workflow`. The backend graph service is deferred (out of scope per CONTEXT.md). The `hybrid_mode` flag must be plumbed into the initial state dict in `run_hedge_fund` (currently absent in `src/main.py`); agents gate themselves via `data.get("hybrid_mode", False)`.

**Primary recommendation:** Implement the three changes in strict dependency order — (1) multiplier chaining in risk_manager, (2) action filtering in portfolio_manager, (3) DAG rewiring in main.py — each with isolated unit tests that mock out the LLM and API calls, following the established `patch("src.agents.X.call_llm")` pattern from Phase 2.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Multiplier chaining (D-26/D-27/D-28) | API / Backend — risk_manager.py | — | Deterministic math belongs in the risk control layer, not in the hybrid agents or portfolio manager |
| Meta-label action suppression (D-32/D-33) | API / Backend — portfolio_manager.py | — | Final execution gate; must run after risk limits are set |
| Meta-label quantity scaling (D-34/D-35) | API / Backend — portfolio_manager.py | — | max_shares is derived from risk_manager output; scaling happens before allowed_actions is computed |
| hybrid_layer DAG composition | API / Backend — main.py create_workflow | — | Graph topology is owned by the workflow builder, not individual agents |
| hybrid_mode state propagation | API / Backend — main.py run_hedge_fund | — | run_hedge_fund constructs the initial AgentState dict; hybrid_mode must be threaded in here |

---

## Standard Stack

No new packages are installed in Phase 3. All necessary dependencies are already present.

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | present | StateGraph DAG, add_node, add_edge | Project's DAG engine; used throughout src/main.py |
| pydantic | present | Schema validation for hybrid outputs | Used by all existing hybrid agent schemas |
| langchain-core | present | HumanMessage, AgentState | Project baseline |

### Supporting (already installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest + unittest.mock | present | Unit tests with mocked LLM | All agent tests; mock `call_llm` per agent module |

**Installation:** None required. `poetry install` covers all dependencies.

---

## Package Legitimacy Audit

No new packages are installed in Phase 3. This section is not applicable.

---

## Architecture Patterns

### System Architecture Diagram

```
START
  |
start_node
  |
  +---> [analyst_1] ---+
  +---> [analyst_2] ---+---> hybrid_layer  (NEW sequential node)
  +---> [analyst_N] ---+         |
                                 |  calls in order:
                                 |    psychological_guardrail_agent(state)
                                 |    consensus_agent(state)
                                 |    debate_agent(state)
                                 |    meta_labeler_agent(state)
                                 |  returns merged state updates
                                 v
                        risk_management_agent  (MODIFIED: reads guardrail + meta_label multipliers)
                                 |
                                 v
                        portfolio_management_agent  (MODIFIED: enforces meta-label action filtering)
                                 |
                                 v
                               END
```

**State data keys flowing through the graph:**

```
state["data"]["analyst_signals"]       — written by analysts, read by guardrail + consensus + risk_manager + portfolio_manager
state["data"]["guardrail_outputs"]     — written by psychological_guardrail_agent, read by risk_manager (NEW)
state["data"]["meta_label_outputs"]    — written by meta_labeler_agent, read by risk_manager (NEW) and portfolio_manager (NEW)
state["data"]["consensus_output"]      — written by consensus_agent (unused in Phase 3)
state["data"]["debate_outputs"]        — written by debate_agent, read by meta_labeler_agent
state["data"]["hybrid_mode"]           — set in run_hedge_fund initial state, read by all hybrid agents and gating checks
```

### Recommended Project Structure

No new directories. Changes are isolated to existing files:

```
src/
├── agents/
│   ├── risk_manager.py          # MODIFIED: multiplier chaining in inner loop
│   ├── portfolio_manager.py     # MODIFIED: meta-label filtering after max_shares
│   ├── psychological_guardrail.py  # unchanged
│   ├── consensus.py             # unchanged
│   ├── debate.py                # unchanged
│   └── meta_labeler.py          # unchanged
├── main.py                      # MODIFIED: hybrid_layer node, DAG rewiring, hybrid_mode in state
tests/agents/
├── test_risk_manager_hybrid.py  # NEW: unit tests for INT-01
└── test_portfolio_manager_hybrid.py  # NEW: unit tests for INT-02
```

### Pattern 1: Hybrid Mode Gate (established in Phase 2)

**What:** All hybrid-sensitive code paths are wrapped in `if not data.get("hybrid_mode", False): return early`.
**When to use:** At the top of any agent function that does hybrid work, and as a guard before reading `guardrail_outputs`/`meta_label_outputs` inside existing agents.

```python
# Source: src/agents/psychological_guardrail.py (lines 32-33) — confirmed from codebase
if not data.get("hybrid_mode", False):
    return {"messages": [], "data": {}}
```

For the new guards inside risk_manager and portfolio_manager, the gate is inline, not an early return (the agents must still produce their full output):

```python
# Pattern for inline guards in risk_manager and portfolio_manager
if data.get("hybrid_mode", False):
    guardrail = data.get("guardrail_outputs", {}).get(ticker, {})
    disagreement_multiplier = float(guardrail.get("confidence_multiplier", 1.0))
    # ... additional reads
else:
    disagreement_multiplier = 1.0
    meta_size_multiplier = 1.0
```

### Pattern 2: Multiplier Chaining in risk_management_agent (INT-01)

**What:** After `position_limit = total_portfolio_value * combined_limit_pct`, multiply in the two new scalars before computing `remaining_position_limit`.
**Apply point:** Exactly as specified in D-30 — `position_limit` gets multiplied, then `remaining_position_limit = position_limit - current_position_value`.

Existing code (lines 162-167 of risk_manager.py):
```python
combined_limit_pct = vol_adjusted_limit_pct * corr_multiplier
position_limit = total_portfolio_value * combined_limit_pct

# Calculate remaining limit for this position
remaining_position_limit = position_limit - current_position_value
```

After INT-01 integration:
```python
combined_limit_pct = vol_adjusted_limit_pct * corr_multiplier
position_limit = total_portfolio_value * combined_limit_pct

# Hybrid multiplier chaining (D-26, D-27, D-28, D-31)
if data.get("hybrid_mode", False):
    guardrail = data.get("guardrail_outputs", {}).get(ticker, {})
    disagreement_multiplier = float(guardrail.get("confidence_multiplier", 1.0))
    meta = data.get("meta_label_outputs", {}).get(ticker, {})
    meta_size_multiplier = float(meta.get("size_multiplier", 1.0))
    position_limit = position_limit * disagreement_multiplier * meta_size_multiplier

# Calculate remaining limit for this position
remaining_position_limit = position_limit - current_position_value
```

The `reasoning` dict in `risk_analysis[ticker]` should also record `disagreement_multiplier` and `meta_size_multiplier` for observability.

### Pattern 3: Meta-Label Filtering in portfolio_management_agent (INT-02)

**What:** After `max_shares` dict is built per ticker (lines 52-55 of portfolio_manager.py), before calling `generate_trading_decision`, inject meta-label filtering.
**Apply point:** D-36 — injected after max_shares is computed, before generate_trading_decision.

The injection site in the existing code (portfolio_manager.py lines 51-79) is the block after the ticker loop that builds `max_shares`. The filtering happens to `max_shares` in place (for reduce/allow) or to `allowed_actions` after `compute_allowed_actions` returns (for suppress/hold_only).

Recommended implementation approach (label dispatch):

```python
# After the for-ticker loop that builds max_shares, before generate_trading_decision
if data.get("hybrid_mode", False):
    meta_label_outputs = data.get("meta_label_outputs", {})
    for ticker in tickers:
        meta = meta_label_outputs.get(ticker, {})
        label = meta.get("label")
        size_mult = float(meta.get("size_multiplier", 1.0))
        allow_trade = meta.get("allow_trade", True)

        if not allow_trade:  # suppress (D-32)
            max_shares[ticker] = 0
        elif label == "hold_only":  # D-33 — handled post compute_allowed_actions
            pass  # mark for post-filter; max_shares unchanged
        elif label in ("reduce", "allow"):  # D-34, D-35
            max_shares[ticker] = int(max_shares[ticker] * size_mult)
```

For `hold_only`, `compute_allowed_actions` still runs with the unmodified `max_shares`, then the result is filtered to remove `buy` and `short` keys. The cleanest approach is to apply a second pass over `allowed_actions_full` after `compute_allowed_actions` is called, before tickers_for_llm is built.

**Important:** `suppress` sets `max_shares[ticker] = 0`, which causes `compute_allowed_actions` to produce `{"hold": 0}` naturally (buy=0 because max_qty=0, short=0 because max_qty=0), satisfying D-32 without special-casing `allowed_actions_full` after the fact.

**Important for hold_only:** The `hold_only` filter must remove `"buy"` and `"short"` from the pruned allowed dict AFTER `compute_allowed_actions` runs, not before. This preserves `sell` and `cover` (exit actions).

### Pattern 4: hybrid_layer Composite Node

**What:** A function in `src/main.py` (or a new `src/agents/hybrid_layer.py`) that calls all four hybrid agents sequentially on the same state and returns a merged state update. LangGraph's `merge_dicts` reducer ensures the returned partial states accumulate correctly.

**Implementation:**

```python
# Source: D-38, D-39, D-40 from CONTEXT.md
def hybrid_layer_node(state: AgentState) -> dict:
    """Composite node: guardrail → consensus → debate → meta_labeler."""
    from src.agents.psychological_guardrail import psychological_guardrail_agent
    from src.agents.consensus import consensus_agent
    from src.agents.debate import debate_agent
    from src.agents.meta_labeler import meta_labeler_agent

    result = {"messages": [], "data": {}}

    for agent_fn in [psychological_guardrail_agent, consensus_agent, debate_agent, meta_labeler_agent]:
        partial = agent_fn(state)
        result["messages"] = result["messages"] + list(partial.get("messages", []))
        result["data"] = {**result["data"], **partial.get("data", {})}
        # Update state so downstream agents in this layer see prior agents' outputs
        state = {**state, "data": {**state["data"], **partial.get("data", {})}, "messages": state["messages"] + list(partial.get("messages", []))}

    return result
```

**Critical state threading note:** Each agent reads `state["data"]` for its inputs (e.g., meta_labeler reads `guardrail_outputs` written by guardrail). Because all four calls happen inside `hybrid_layer_node` before LangGraph applies the merge, the state must be manually threaded between calls — the merged result from each prior agent must be written into the local `state` variable before the next agent call. If this is not done, meta_labeler will not see `guardrail_outputs` because LangGraph's reducer has not yet run.

**DAG rewiring in create_workflow:**

Existing:
```python
for analyst_key in selected_analysts:
    node_name = analyst_nodes[analyst_key][0]
    workflow.add_edge(node_name, "risk_management_agent")
```

After:
```python
workflow.add_node("hybrid_layer", hybrid_layer_node)

for analyst_key in selected_analysts:
    node_name = analyst_nodes[analyst_key][0]
    workflow.add_edge(node_name, "hybrid_layer")

workflow.add_edge("hybrid_layer", "risk_management_agent")
```

**hybrid_mode plumbing in run_hedge_fund:** The `hybrid_mode` flag is not currently passed into the initial state dict. It must be added as a parameter to `run_hedge_fund` and injected into `state["data"]`:

```python
def run_hedge_fund(
    tickers, start_date, end_date, portfolio,
    show_reasoning=False, selected_analysts=None,
    model_name="gpt-4.1", model_provider="OpenAI",
    hybrid_mode=False,   # NEW
    debate_mode=False,   # NEW (optional, for future use)
):
    ...
    final_state = agent.invoke({
        ...
        "data": {
            "tickers": tickers,
            "portfolio": portfolio,
            "start_date": start_date,
            "end_date": end_date,
            "analyst_signals": {},
            "hybrid_mode": hybrid_mode,    # NEW
            "debate_mode": debate_mode,    # NEW
        },
        ...
    })
```

### Anti-Patterns to Avoid

- **Re-computing disagreement score in risk_manager:** D-27 explicitly forbids this. The guardrail agent already ran `compute_disagreement_multiplier` and stored its result as `confidence_multiplier`. Reading it directly avoids duplication and keeps risk_manager thin.
- **Building meta-label filtering into compute_allowed_actions:** `compute_allowed_actions` is a pure function with no state coupling. Injecting hybrid logic there would break the clean separation and make it harder to unit-test the function in isolation. Filter `max_shares` before the call (reduce/allow/suppress), filter `allowed_actions` after the call (hold_only).
- **Conditional graph building for hybrid_mode:** D-40 forbids this. Always add `hybrid_layer`; let agents gate themselves.
- **Threading state in hybrid_layer by reference only:** Python dicts are mutable, but LangGraph's state is a TypedDict. Always create a new merged state dict for each subsequent agent call within the composite node.
- **Not updating the reasoning dict in risk_analysis:** The `reasoning` sub-dict in risk_analysis is logged and serialized to the message. Adding `disagreement_multiplier` and `meta_size_multiplier` fields there makes the hybrid adjustment observable in output without adding new top-level keys.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| State merging between sequential agents in hybrid_layer | Custom accumulator class | Manual dict merge + state threading (see Pattern 4) | LangGraph's merge_dicts reducer only runs between graph steps, not within a single node function; simple dict merge is correct |
| Allowed-actions filtering for hold_only | New compute_allowed_actions variant | Post-filter on the existing return value | compute_allowed_actions is pure and tested; a post-filter preserves its invariants |
| Neutral multiplier fallback | Separate code path | `.get("key", 1.0)` with default 1.0 | D-31 and D-37 specify neutral multiplier = 1.0; default-value get is idiomatic and zero-overhead |
| CPPI integration | Apply drawdown_guardrail.py | Deferred to Phase 4 — do not touch | D-29 explicitly defers this; no floor tracking yet |

**Key insight:** The entire phase is integration work, not new algorithm development. All the math already exists in Phase 1 risk utilities and Phase 2 agent outputs. The work is reading the right keys, applying them at the right point in the existing flow, and guarding with the established hybrid_mode gate pattern.

---

## Common Pitfalls

### Pitfall 1: State Not Threaded Between hybrid_layer Sub-Calls

**What goes wrong:** meta_labeler_agent reads `state["data"]["guardrail_outputs"]` but finds an empty dict because the guardrail's return value was accumulated in the composite node's local result but not written back into the state dict passed to subsequent agents.

**Why it happens:** LangGraph's merge_dicts reducer only runs between full graph steps (after a node function returns). Within a single node function, the caller is responsible for threading state updates between sequential calls.

**How to avoid:** After each agent call inside `hybrid_layer_node`, merge the returned `data` dict into the `state["data"]` dict before calling the next agent:
```python
state = {**state, "data": {**state["data"], **partial.get("data", {})}}
```

**Warning signs:** meta_label_outputs all default to "allow" with size_multiplier=1.0 even when guardrail outputs indicate suppression conditions.

### Pitfall 2: Applying Multipliers to combined_limit_pct Instead of position_limit

**What goes wrong:** Multiplying `disagreement_multiplier` into `combined_limit_pct` instead of `position_limit` changes the semantics — `combined_limit_pct` is a percentage, but the multipliers should be applied to the dollar amount to match D-30.

**Why it happens:** The existing code computes `combined_limit_pct` then converts to `position_limit`. It is tempting to chain multipliers before the conversion.

**How to avoid:** Per D-30, the apply point is `position_limit` (after the dollar conversion). The line `position_limit = total_portfolio_value * combined_limit_pct` is followed immediately by the hybrid multiplier block.

**Warning signs:** Position limits shrink more than expected; the reasoning dict shows correct multipliers but the limit is wrong by a factor of `total_portfolio_value`.

### Pitfall 3: hold_only Incorrectly Blocks Exit Actions

**What goes wrong:** When filtering for `hold_only`, removing all actions including `sell` and `cover`. This is `suppress` behavior, not `hold_only`.

**Why it happens:** Confusion between D-32 (suppress = no trades) and D-33 (hold_only = exits only).

**How to avoid:** Per D-33, `hold_only` keeps `sell` and `cover` in the allowed dict but removes `buy` and `short`. The filter is:
```python
if label == "hold_only":
    for key in ("buy", "short"):
        allowed[ticker].pop(key, None)
```

**Warning signs:** Tests for hold_only pass when a long position exists (sell is present) but a portfolio with no existing position cannot close any positions.

### Pitfall 4: suppress Does Not Zero Out via max_shares

**What goes wrong:** Setting `max_shares[ticker] = 0` does not suppress sell/cover actions because those are driven by `long_shares` and `short_shares` from the portfolio positions, not from `max_qty`.

**Why it happens:** `compute_allowed_actions` allows `sell = long_shares` and `cover = short_shares` regardless of `max_qty`. Setting max_shares to 0 only prevents new buys and shorts.

**How to avoid:** Per D-32, suppress must override the entire allowed dict to `{"hold": 0}` AFTER `compute_allowed_actions` runs. A second pass over `allowed_actions_full` is needed:
```python
if not allow_trade:  # suppress
    allowed_actions_full[ticker] = {"hold": 0}
```

**Warning signs:** A suppressed ticker still shows sell/cover in the LLM prompt, and the LLM picks an exit action.

### Pitfall 5: hybrid_mode Not in Initial State Dict

**What goes wrong:** All four hybrid agents return early (`return {"messages": [], "data": {}}`) because `data.get("hybrid_mode", False)` is False, making the hybrid layer a silent no-op even when hybrid mode is intended.

**Why it happens:** `hybrid_mode` is not currently threaded into the initial state in `run_hedge_fund`. It must be added as a parameter and written into `state["data"]`.

**How to avoid:** Add `hybrid_mode=False` parameter to `run_hedge_fund` and inject it:
```python
"data": {
    ...
    "hybrid_mode": hybrid_mode,
    "debate_mode": debate_mode,
}
```

**Warning signs:** All guardrail/meta_label outputs are absent from final state; risk_manager uses only vol/corr multipliers even when hybrid_mode=True was intended.

### Pitfall 6: meta_label suppress with size_multiplier=0.0 in Risk Manager

**What goes wrong:** Risk manager reads `meta_label_outputs[ticker]["size_multiplier"]` for a suppressed ticker and gets `0.0`, making `position_limit = 0.0`. This is correct behavior — but it interacts with the portfolio_manager because `remaining_position_limit = 0.0 - current_position_value` becomes negative, which then flows through `max_position_size = min(remaining, cash) = min(negative, positive)`, resulting in a negative max_position_size.

**Why it happens:** The risk_manager computes `remaining_position_limit = position_limit - current_position_value`. If current_position_value > 0 and position_limit = 0, the remaining limit is negative.

**How to avoid:** The existing code already has `max_position_size = min(remaining_position_limit, portfolio.get("cash", 0))` which produces 0 or negative. Portfolio manager then computes `max_shares = int(0 // price) = 0` or `int(negative // price) = negative integer`. Verify that `int(position_limits[ticker] // current_prices[ticker])` with a negative position_limit produces 0 (not a negative number) via `max(0, int(...))` guard. This may require a `max(0, ...)` guard in portfolio_manager's max_shares computation (line 53 of portfolio_manager.py currently uses `int(position_limits[ticker] // current_prices[ticker])` without a zero floor).

**Warning signs:** Tests with a suppressed ticker that has an existing position produce negative max_shares, and the LLM sees `{"sell": N, "cover": M, "buy": -5}` in the allowed dict.

---

## Code Examples

Verified patterns from codebase inspection:

### Risk Manager Inner Loop — Existing Structure (confirmed from src/agents/risk_manager.py lines 130-193)
```python
# Existing
combined_limit_pct = vol_adjusted_limit_pct * corr_multiplier
position_limit = total_portfolio_value * combined_limit_pct

# D-30 INSERT HERE: apply hybrid multipliers to position_limit

remaining_position_limit = position_limit - current_position_value
max_position_size = min(remaining_position_limit, portfolio.get("cash", 0))
```

### Portfolio Manager Injection Point (confirmed from src/agents/portfolio_manager.py lines 51-79)
```python
# After this loop completes:
for ticker in tickers:
    ...
    max_shares[ticker] = int(position_limits[ticker] // current_prices[ticker])
    ...

# D-36 INSERT HERE: meta-label filtering on max_shares (and post-filter on allowed_actions)

state["data"]["current_prices"] = current_prices
result = generate_trading_decision(
    tickers=tickers,
    signals_by_ticker=signals_by_ticker,
    current_prices=current_prices,
    max_shares=max_shares,     # modified by meta-label filtering
    portfolio=portfolio,
    agent_id=agent_id,
    state=state,
)
```

### Test State Builder (confirmed from tests/agents/conftest.py)
```python
# Source: tests/agents/conftest.py _make_empty_state
from tests.agents.conftest import _make_empty_state

def _make_state(tickers=None, hybrid_mode=True, guardrail_outputs=None, meta_label_outputs=None):
    state = _make_empty_state(tickers=tickers or ["AAPL"])
    state["data"]["hybrid_mode"] = hybrid_mode
    state["data"]["guardrail_outputs"] = guardrail_outputs or {}
    state["data"]["meta_label_outputs"] = meta_label_outputs or {}
    return state
```

### Mock Pattern for Agent Tests (confirmed from tests/agents/test_meta_labeler.py)
```python
# Source: tests/agents/test_meta_labeler.py
from unittest.mock import patch

with patch("src.agents.risk_manager.call_llm", side_effect=_fake_llm):
    result = risk_management_agent(state)
```

Note: risk_manager does not call `call_llm` directly — it calls `get_prices` and other API functions. Tests should mock `src.tools.api.get_prices` and `src.tools.api.prices_to_df` (or use the existing `mock_api_calls` fixture from conftest.py) rather than mocking call_llm.

### LangGraph Edge Rewiring (confirmed from src/main.py lines 104-118)
```python
# Existing (before Phase 3)
for analyst_key in selected_analysts:
    node_name = analyst_nodes[analyst_key][0]
    workflow.add_edge(node_name, "risk_management_agent")

workflow.add_edge("risk_management_agent", "portfolio_manager")

# After Phase 3
workflow.add_node("hybrid_layer", hybrid_layer_node)
for analyst_key in selected_analysts:
    node_name = analyst_nodes[analyst_key][0]
    workflow.add_edge(node_name, "hybrid_layer")

workflow.add_edge("hybrid_layer", "risk_management_agent")
workflow.add_edge("risk_management_agent", "portfolio_manager")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Analysts fan directly into risk_manager | Analysts → hybrid_layer → risk_manager | Phase 3 | hybrid_layer intercepts all signals before risk sizing |
| risk_manager uses only vol + corr multipliers | risk_manager multiplies in disagreement + meta_size multipliers | Phase 3 | INT-01: hybrid engine has sizing authority |
| portfolio_manager passes all actions to LLM | portfolio_manager gates actions by meta-label before LLM call | Phase 3 | INT-02: meta-label has execution authority |

**Deprecated/outdated:**

- Direct `[analyst] → risk_management_agent` edges in `create_workflow`: replaced by `[analyst] → hybrid_layer` edges after Phase 3. Any test that asserts the old edge topology will need updating.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | suppress label sets size_multiplier=0.0 in MetaLabelOutput (deduced from meta_labeler.py line 57) | Pitfall 6, Pattern 3 | If 0.0 is not the actual value, the negative remaining_position_limit edge case does not occur |
| A2 | The backend `app/backend/services/graph.py::create_graph` is OUT OF SCOPE for Phase 3 — only `src/main.py::create_workflow` is modified | Architecture Patterns | If the backend graph also needs hybrid_layer, Plan 03-03 would be needed |

**A1 is confirmed from codebase** — `meta_labeler.py` line 56-57: `label = "suppress"; size_multiplier = 0.0`. Not truly assumed.
**A2 is confirmed by CONTEXT.md deferred section:** "Web app graph: the React Flow visualization of the hybrid_layer node — deferred."

All claims in this research were verified from codebase source or CONTEXT.md locked decisions. The assumptions log is effectively empty.

---

## Open Questions

1. **max_shares floor guard for suppress with existing position**
   - What we know: `int(negative_value // price)` in Python rounds toward negative infinity, producing a negative integer. The existing `max_shares` computation has no `max(0, ...)` guard.
   - What's unclear: Whether the existing test suite covers this edge case or whether it is caught by the `min(remaining, cash)` path.
   - Recommendation: Add `max(0, int(position_limits[ticker] // current_prices[ticker]))` in portfolio_manager.py line 53 as a defensive guard. This is a safe change with no behavior impact when position_limit >= 0.

2. **Does create_workflow need a hybrid_mode parameter?**
   - What we know: D-40 says hybrid_layer is always added. D-31/D-37 say agents gate themselves via the state dict. create_workflow does not need to know about hybrid_mode.
   - What's unclear: Whether callers outside run_hedge_fund (e.g., the backtester) also need hybrid_mode plumbed.
   - Recommendation: Add hybrid_mode only to run_hedge_fund for Phase 3. Backtester integration is Phase 4 scope.

---

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified — Phase 3 is code-only changes to existing agents and graph wiring, no new tools, services, or CLIs required).

---

## Validation Architecture

`workflow.nyquist_validation` is `false` in `.planning/config.json`. This section is omitted per config.

---

## Security Domain

### Applicable ASVS Categories

`security_enforcement: true` in `.planning/config.json`.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Multiplier values read from state dicts should be validated as floats in [0.0, 1.0]; use `float(...)` with fallback to 1.0 (already specified in D-31) |
| V6 Cryptography | no | — |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed state data injecting NaN or Inf into multiplier chain | Tampering | Cast with `float(...) or 1.0`; note Python's `float("nan") * x` propagates silently — use explicit `math.isfinite` check or `min(max(val, 0.0), 1.0)` clamp |
| Negative size_multiplier from corrupt state | Tampering | Clamp to [0.0, 1.0]: `max(0.0, min(1.0, float(meta.get("size_multiplier", 1.0))))` |
| suppress label bypass via missing allow_trade key | Elevation of Privilege | Check `meta.get("allow_trade", True)` — default True means if the key is absent, suppress is NOT triggered (safe default: allow trade) |

The most important security control in this phase is **defensive defaults**: absent hybrid data should mean no restriction (neutral multiplier = 1.0, allow_trade = True), not maximum restriction. This prevents a data corruption bug from silently zeroing out all trading.

---

## Sources

### Primary (HIGH confidence)
- `src/agents/risk_manager.py` — confirmed exact apply point, existing multiplier chain, reasoning dict structure
- `src/agents/portfolio_manager.py` — confirmed max_shares computation, compute_allowed_actions, generate_trading_decision call site
- `src/agents/meta_labeler.py` — confirmed label values, size_multiplier values, state output key
- `src/agents/psychological_guardrail.py` — confirmed confidence_multiplier output key, state output key `guardrail_outputs`
- `src/main.py` — confirmed create_workflow edge pattern, run_hedge_fund initial state dict (confirmed hybrid_mode is absent)
- `src/graph/state.py` — confirmed merge_dicts reducer behavior (last-write-wins per key)
- `tests/agents/conftest.py` — confirmed _make_empty_state, mock_api_calls fixture
- `tests/agents/test_meta_labeler.py` — confirmed test pattern (patch call_llm per module)
- `.planning/phases/03-sizing-execution-integrations/03-CONTEXT.md` — all locked decisions D-26 through D-40

### Secondary (MEDIUM confidence)
- `app/backend/services/graph.py` — confirmed backend graph is independent from src/main.py and not in scope for Phase 3
- `.planning/config.json` — confirmed nyquist_validation=false, security_enforcement=true

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages, all dependencies confirmed installed
- Architecture: HIGH — all apply points confirmed from live codebase inspection; no training-data guesses
- Pitfalls: HIGH — derived from actual code paths in the live codebase, not hypothetical
- Integration patterns: HIGH — all four hybrid agents confirmed present and operational from Phase 2

**Research date:** 2026-06-09
**Valid until:** 2026-07-09 (stable internal codebase; no external dependency churn risk)
