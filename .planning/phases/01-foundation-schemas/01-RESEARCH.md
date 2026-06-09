# Phase 1: Foundation & Schemas - Research

**Researched:** 2026-06-08
**Domain:** Pydantic v2 schemas, pure-math risk utilities, pytest baseline verification
**Confidence:** HIGH

## Summary

Phase 1 is a pure greenfield addition — no existing code is changed, only new files are created under `src/schemas/`, `src/risk/`, and `tests/`. The baseline (417 tests, 0 failures) must remain intact when the phase completes.

The critical discovery is that **`src/schemas/hybrid.py` and `tests/schemas/test_hybrid.py` already exist and pass 36 tests**. SCHM-01 is therefore already substantially complete; the plan only needs to verify the file is correct and add the missing `model_config = ConfigDict(extra="ignore")` required by D-12. The three risk utility modules (`src/risk/disagreement.py`, `src/risk/drawdown_guardrail.py`, `src/risk/sizing.py`) do not exist and must be created from scratch.

All math must be pure Python with no LLM, no I/O, and no pandas/numpy dependencies — deterministic helpers callable from any agent or test without an event loop.

**Primary recommendation:** Create `src/risk/__init__.py` and three risk utility modules with pure-math functions; patch the one missing schema config; write tests for all three risk modules. No agent code changes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Represent analyst recommendations numerically: Buy=+1, Hold/Neutral=0, Sell=-1.
- **D-02:** Disagreement score = normalized standard deviation of stances; max std = 50/50 buy/sell split. Multiplier = 1.0 - disagreement_score.
- **D-03:** Missing/null analyst signals imputed as 0 (Hold/Neutral) in the std calculation.
- **D-04:** CPPI drawdown floor = Peak Value * (1 - max_drawdown_limit); trailing peak model.
- **D-05:** CPPI risk multiplier = Cushion / (Max Drawdown Limit * Peak Value), capped at 1.0.
- **D-06:** max_drawdown_limit configurable via state['data']['max_drawdown_limit'], default 0.20.
- **D-07:** Peak portfolio value persisted in state['data']['portfolio']['peak_value'].
- **D-08:** Kelly helper receives win_probability (p) and win_loss_ratio (b) as explicit parameters.
- **D-09:** Quarter Kelly (0.25 multiplier), hard cap at 25% of total portfolio value.
- **D-10:** Kelly helper disabled by default via `enabled: bool = False`; returns 1.0 when disabled.
- **D-11:** Kelly allocation floored at 0.0 (no negatives).
- **D-12:** Pydantic models ignore/drop extra JSON fields silently (`extra="ignore"`).
- **D-13:** HybridDecisionTrace contains ticker, timestamp(?), regime, selected_agents, debate, guardrails, meta_label, reasoning_summary.
- **D-14:** Optional fields as `FieldType | None = None`.
- **D-15:** All JSON key casing as snake_case.

### Claude's Discretion
- Internal function naming and standard test setups.

### Deferred Ideas (OUT OF SCOPE)
- None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCHM-01 | Define structured Pydantic models in `src/schemas/hybrid.py` | File already exists with 7 models; needs `extra="ignore"` config per D-12; D-13 implies adding `timestamp` and `reasoning_summary` to HybridDecisionTrace |
| RISK-01 | Deterministic disagreement score in `src/risk/disagreement.py` | Pure Python std calculation; Buy=+1, Hold=0, Sell=-1; normalized against max possible std |
| RISK-02 | CPPI drawdown multiplier in `src/risk/drawdown_guardrail.py` | Trailing Peak Floor model; cushion-based linear scaling; max_drawdown_limit configurable |
| RISK-03 | Fractional Kelly helper in `src/risk/sizing.py` | Quarter Kelly, 25% cap, floor 0.0, disabled by default |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Pydantic schemas | `src/schemas/` module | Consumed by all layers | Schemas are shared contracts; no business logic |
| Disagreement math | `src/risk/` pure functions | Called by guardrail agent (Phase 2) | Math has no I/O dependency; belongs in risk layer |
| CPPI drawdown math | `src/risk/` pure functions | Called by risk_manager (Phase 6) | Same pure-math isolation principle |
| Kelly sizing math | `src/risk/` pure functions | Called by portfolio_manager (Phase 7) | Disabled by default; no active integration this phase |
| Tests | `tests/schemas/`, `tests/risk/` | — | Co-located with corresponding source module |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | ^2.4.2 (installed: 2.13.4) | Schema definition and validation | Already in project; v2 API confirmed |
| pytest | ^8.3 | Test runner | Already in project |
| math (stdlib) | — | sqrt for std calculation | No extra dependency; deterministic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing (stdlib) | — | Type annotations for all new code | Required for Pydantic v2 and mypy compliance |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib math.sqrt | numpy | numpy is heavier; pure math needs no numpy for scalar ops |
| manual std calc | statistics.stdev | Either works; statistics module is slightly cleaner, both stdlib |

**Installation:** No new packages required. All dependencies already present.

## Package Legitimacy Audit

No new packages are introduced in this phase. The phase uses only already-installed project dependencies (pydantic 2.13.4, pytest 8.x) and Python stdlib.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
[src/schemas/hybrid.py]     (already exists — patch only)
        |
        v
[src/risk/disagreement.py]  NEW — pure function: compute_disagreement_score(stances) -> float
[src/risk/drawdown_guardrail.py]  NEW — pure functions: compute_cppi_multiplier(...) -> float
[src/risk/sizing.py]        NEW — pure function: fractional_kelly(..., enabled=False) -> float
        |
        v
[tests/schemas/test_hybrid.py]  (already exists — 36 passing tests)
[tests/risk/test_disagreement.py]   NEW
[tests/risk/test_drawdown_guardrail.py]  NEW
[tests/risk/test_sizing.py]   NEW
```

Data flows upward in later phases; this phase only establishes the building blocks.

### Recommended Project Structure
```
src/
├── schemas/
│   └── hybrid.py            # patch: add ConfigDict(extra="ignore") + missing D-13 fields
├── risk/
│   ├── __init__.py          # new: empty or re-exports
│   ├── disagreement.py      # new: RISK-01
│   ├── drawdown_guardrail.py # new: RISK-02
│   └── sizing.py            # new: RISK-03
tests/
├── schemas/
│   └── test_hybrid.py       # already exists — may need 1-2 extra tests for D-12 and D-13
└── risk/
    ├── __init__.py           # new: empty
    ├── test_disagreement.py  # new
    ├── test_drawdown_guardrail.py  # new
    └── test_sizing.py        # new
```

### Pattern 1: Pure Deterministic Math Functions

**What:** Stateless functions taking only scalar/list arguments; no I/O, no LLM, no pandas.
**When to use:** All RISK-01/02/03 implementations.
**Example:**
```python
# Source: CONTEXT.md D-01, D-02, D-03
from math import sqrt

def compute_disagreement_score(stances: list[int | None]) -> float:
    """
    Compute normalized disagreement score from analyst stances.
    Buy=+1, Hold/Neutral=0, Sell=-1. None imputed as 0.
    Returns float in [0.0, 1.0]; multiplier = 1.0 - score.
    """
    values = [s if s is not None else 0 for s in stances]
    if len(values) < 2:
        return 0.0
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std = sqrt(variance)
    # Maximum possible std for stances in {-1, 0, +1} is 1.0 (50/50 Buy/Sell split)
    return min(std, 1.0)
```

### Pattern 2: Pydantic v2 ConfigDict for Extra Field Tolerance

**What:** Apply `model_config = ConfigDict(extra="ignore")` to all hybrid models.
**When to use:** D-12 requires all models to silently drop unexpected LLM output fields.
**Example:**
```python
# Source: CONTEXT.md D-12; Pydantic v2 docs
from pydantic import BaseModel, ConfigDict

class RegimeClassification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # ... fields unchanged
```

### Pattern 3: CPPI Cushion Multiplier

**What:** Pure function returning float multiplier [0.0, 1.0].
**When to use:** RISK-02.
**Example:**
```python
# Source: CONTEXT.md D-04, D-05, D-06
def compute_cppi_multiplier(
    portfolio_value: float,
    peak_value: float,
    max_drawdown_limit: float = 0.20,
) -> float:
    """
    Returns CPPI risk multiplier in [0.0, 1.0].
    Floor = peak_value * (1 - max_drawdown_limit).
    Multiplier = Cushion / (max_drawdown_limit * peak_value), capped at 1.0.
    """
    floor = peak_value * (1.0 - max_drawdown_limit)
    cushion = portfolio_value - floor
    if cushion <= 0 or peak_value <= 0 or max_drawdown_limit <= 0:
        return 0.0
    denominator = max_drawdown_limit * peak_value
    return min(cushion / denominator, 1.0)
```

### Pattern 4: Fractional Kelly Helper

**What:** Pure function; disabled by default; floored at 0.0; capped at 0.25.
**When to use:** RISK-03.
**Example:**
```python
# Source: CONTEXT.md D-08, D-09, D-10, D-11
def fractional_kelly(
    win_probability: float,
    win_loss_ratio: float,
    enabled: bool = False,
) -> float:
    """
    Returns Quarter Kelly fraction in [0.0, 0.25].
    Returns 1.0 when disabled (neutral multiplier, no effect on sizing).
    """
    if not enabled:
        return 1.0
    # Full Kelly: f = (p * b - q) / b  where q = 1 - p
    q = 1.0 - win_probability
    full_kelly = (win_probability * win_loss_ratio - q) / win_loss_ratio
    quarter_kelly = max(full_kelly * 0.25, 0.0)
    return min(quarter_kelly, 0.25)
```

### Anti-Patterns to Avoid
- **Changing agent code:** Phase 1 is additive only. risk_manager.py and portfolio_manager.py must not be touched.
- **numpy/pandas in risk utilities:** These are pure scalar math helpers. Import only stdlib.
- **Shared global state:** All functions are stateless; CPPI peak tracking is handled by the caller (risk_manager), not the utility.
- **Pydantic v1 API usage:** `dict()`, `parse_obj()`, `class Config` are removed in v2. Use `model_dump()`, `model_validate()`, `ConfigDict`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON serialization | Custom serializer | `model.model_dump_json()` | Pydantic v2 handles datetime, Literal, nested models |
| Field bounds validation | Manual if-checks in `__init__` | `Field(ge=0, le=100)` | Pydantic validates at parse time; raises ValidationError |
| Optional field handling | `hasattr` checks | `Optional[T] = None` / `T \| None = None` | Pydantic v2 null handling is idiomatic |

**Key insight:** The Pydantic schema layer is already 95% complete. The risk math is 3 small pure functions. The entire phase is writing ~150 lines of new code plus tests.

## Common Pitfalls

### Pitfall 1: SCHM-01 Partially Done — Don't Re-Create
**What goes wrong:** Planner schedules a task to "create src/schemas/hybrid.py" when it already exists with 36 passing tests.
**Why it happens:** Requirement says "define structured Pydantic models" but the file was pre-created in a prior session.
**How to avoid:** Wave 0 task must verify file exists and run `pytest tests/schemas/ -q` before any schema work. Only patch the `extra="ignore"` config and verify D-13 fields are present.
**Warning signs:** pytest reports 0 tests collected from tests/schemas/ — file was accidentally deleted.

### Pitfall 2: D-13 Field Gap in HybridDecisionTrace
**What goes wrong:** The existing `HybridDecisionTrace` schema is missing `timestamp` and `reasoning_summary` fields described in D-13.
**Why it happens:** The model was created before the context discussion.
**How to avoid:** The patch task must add `timestamp: datetime | None = None` and `reasoning_summary: str | None = None` with appropriate imports.
**Warning signs:** Serialization test for full trace fails to include these fields.

### Pitfall 3: Disagreement Score Normalization
**What goes wrong:** Returning raw std (max ~1.0 for {-1, +1} split) but not confirming the normalization boundary.
**Why it happens:** For a list of only +1 and -1 values, the population std equals 1.0. But with Hold (0) values mixed in, std drops. The decision says max std = 1.0 (50/50 Buy/Sell split) — correct only for population std, not sample std.
**How to avoid:** Use population std (divide by N, not N-1). Confirm max std = 1.0 with a test case of `[+1, +1, -1, -1]`.
**Warning signs:** Test for max disagreement returns > 1.0 or the multiplier goes negative.

### Pitfall 4: CPPI Zero-Division When Peak Is Zero
**What goes wrong:** Division by zero in `compute_cppi_multiplier` when `peak_value` is 0.0 at the start of a backtest.
**Why it happens:** New portfolio starts with `peak_value = 0` until it is initialized.
**How to avoid:** Guard: `if peak_value <= 0: return 1.0` (no drawdown protection needed yet).

### Pitfall 5: Kelly Returns 1.0 When Disabled — Not 0.0
**What goes wrong:** Returning 0.0 when disabled (blocks all trades) rather than 1.0 (neutral no-op).
**Why it happens:** "disabled" is confused with "zero allocation."
**How to avoid:** D-10 is explicit: `return 1.0` when `enabled=False`. Tests must verify this.

## Code Examples

### Disagreement Multiplier (complete)
```python
# Source: CONTEXT.md D-01 through D-03
from math import sqrt

def compute_disagreement_score(stances: list[int | None]) -> float:
    values = [s if s is not None else 0 for s in stances]
    if len(values) < 2:
        return 0.0
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return min(sqrt(variance), 1.0)

def compute_disagreement_multiplier(stances: list[int | None]) -> float:
    return 1.0 - compute_disagreement_score(stances)
```

### HybridDecisionTrace patch (D-12, D-13)
```python
# Source: CONTEXT.md D-12, D-13, D-14, D-15
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class HybridDecisionTrace(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ticker: str
    timestamp: datetime | None = None
    regime: RegimeClassification | None = None
    selected_agents: list[str] = Field(default_factory=list)
    debate: DebateOutput | None = None
    guardrails: GuardrailOutput | None = None
    meta_label: MetaLabelOutput | None = None
    reasoning_summary: str | None = None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic `class Config` | `model_config = ConfigDict(...)` | Pydantic v2 (2023) | All new models must use ConfigDict |
| `model.dict()` | `model.model_dump()` | Pydantic v2 | `.dict()` raises AttributeError in v2 |
| `Model.parse_obj({})` | `Model.model_validate({})` | Pydantic v2 | Existing tests already use v2 API |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Population std (divide by N) is the correct normalization to achieve max=1.0 for 50/50 split | Standard Stack / Code Examples | Disagreement score could exceed 1.0 or multiplier go negative; fix by clamping |
| A2 | `timestamp` and `reasoning_summary` are the two fields implied by D-13 that are missing from the existing schema | Pitfall 2 | Minor: may need different field names |

## Open Questions

1. **HybridDecisionTrace `timestamp` field type**
   - What we know: D-13 mentions "timestamp" as a field
   - What's unclear: Whether it's `datetime`, `str`, or a custom type
   - Recommendation: Use `datetime | None = None` — serializes cleanly to ISO-8601 via Pydantic

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pydantic | SCHM-01 schemas | ✓ | 2.13.4 | — |
| pytest | All tests | ✓ | ^8.3 | — |
| Python stdlib math | RISK-01/02/03 | ✓ | 3.11+ | — |
| Python stdlib statistics | RISK-01 (alt) | ✓ | 3.11+ | use math.sqrt instead |

**Missing dependencies with no fallback:** none

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ^8.3 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `poetry run pytest tests/schemas/ tests/risk/ -q --no-cov` |
| Full suite command | `poetry run pytest --cov` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCHM-01 | All 7 models validate and serialize; extra fields ignored | unit | `poetry run pytest tests/schemas/ -q --no-cov` | ✅ (36 tests pass) |
| SCHM-01 D-12 | Extra JSON fields silently dropped | unit | included in above | ❌ Wave 0 — add 1 test |
| RISK-01 | Disagreement score in [0,1]; multiplier = 1.0 - score; None imputed as 0 | unit | `poetry run pytest tests/risk/test_disagreement.py -q --no-cov` | ❌ Wave 0 |
| RISK-02 | CPPI multiplier in [0,1]; approaches 0 as value approaches floor | unit | `poetry run pytest tests/risk/test_drawdown_guardrail.py -q --no-cov` | ❌ Wave 0 |
| RISK-03 | Kelly disabled returns 1.0; enabled returns Quarter Kelly ≤ 0.25; floored at 0 | unit | `poetry run pytest tests/risk/test_sizing.py -q --no-cov` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `poetry run pytest tests/schemas/ tests/risk/ -q --no-cov`
- **Per wave merge:** `poetry run pytest -q --no-cov` (full 417+ suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/risk/__init__.py` — empty, required for pytest discovery
- [ ] `tests/risk/test_disagreement.py` — covers RISK-01
- [ ] `tests/risk/test_drawdown_guardrail.py` — covers RISK-02
- [ ] `tests/risk/test_sizing.py` — covers RISK-03
- [ ] 1 extra test in `tests/schemas/test_hybrid.py` — covers D-12 extra-field behavior

## Security Domain

ASVS categories not applicable to this phase. This phase introduces:
- No network endpoints
- No authentication/session/access control
- No cryptography
- No user input validation beyond Pydantic field bounds (already enforced by framework)
- No subprocess, shell, or file I/O

`security_enforcement` is not explicitly configured; by default, bandit applies. The only relevant check is B101 (assert in tests) which is expected and acceptable. The risk math functions contain no security-sensitive operations.

## Sources

### Primary (HIGH confidence)
- Codebase grep: `src/schemas/hybrid.py` — 7 Pydantic models confirmed present, 36 tests passing [VERIFIED: local filesystem]
- Codebase grep: `src/risk/` — directory does not exist [VERIFIED: local filesystem]
- `pydantic.__version__` — 2.13.4 confirmed [VERIFIED: runtime check]
- `poetry run pytest` — 417 tests passing, 0 failures [VERIFIED: runtime check]
- CONTEXT.md — locked decisions D-01 through D-15 [VERIFIED: project file]

### Secondary (MEDIUM confidence)
- Pydantic v2 `ConfigDict(extra="ignore")` pattern [CITED: .claude/rules/fastapi-pydantic-httpx-ruleset.md]
- Population std for normalization analysis [ASSUMED: mathematical reasoning]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pydantic version verified at runtime; no new packages
- Architecture: HIGH — existing file structure confirmed by filesystem probe
- Pitfalls: HIGH — schema gap (D-12 ConfigDict, D-13 fields) confirmed by reading actual source
- Math formulas: HIGH — locked decisions provide exact formulas; only normalization edge case is ASSUMED

**Research date:** 2026-06-08
**Valid until:** 2026-07-08 (stable domain — pydantic version won't change within project)
