# Phase 1: Foundation & Schemas - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-09
**Phase:** 1-Foundation & Schemas
**Areas discussed:** Stance Representation and Disagreement Metric, CPPI Drawdown Floor Definition, Kelly Sizing Inputs, Pydantic Schema Extensibility

---

## Stance Representation and Disagreement Metric

### Question 1: How should we represent analyst recommendations to calculate the disagreement score?
| Option | Description | Selected |
|--------|-------------|----------|
| Numerical mapping | Map Buy to +1, Hold/Neutral to 0, Sell to -1 (enables standard deviation and standard vector distance metrics) | ✓ |
| Categorical mapping | Treat them as categorical values (Buy, Hold, Sell) and compute consensus percentage or entropy-based disagreement | |
| Custom mapping | Implement a continuous scale (e.g. confidence * direction) where each analyst outputs a float between -1.0 and 1.0 | |

**User's choice:** Numerical mapping (Buy = +1, Hold/Neutral = 0, Sell = -1)

---

### Question 2: Which mathematical metric should we use to calculate the ticker's disagreement score?
| Option | Description | Selected |
|--------|-------------|----------|
| Standard Deviation | Calculate the standard deviation of stances across analysts, normalized to [0, 1] (maximum std dev is when analysts are split 50/50 between Buy and Sell) | ✓ |
| Pairwise Distance | Calculate the average absolute difference between all pairs of analyst stances (ranges from 0.0 for total agreement to 2.0 for total split) | |
| Stance Dispersion | Calculate the standard deviation of only non-neutral analyst stances, flagging total division | |

**User's choice:** Standard Deviation (normalized to [0, 1])

---

### Question 3: How should the disagreement calculation handle missing or null analyst signals?
| Option | Description | Selected |
|--------|-------------|----------|
| Impute as Neutral | Treat missing/null signals as Hold/Neutral (0) and include them in the standard deviation calculation (avoids ignoring missing votes) | ✓ |
| Subset Standard Deviation | Calculate the standard deviation only over the active/returned analyst signals, requiring a minimum of 2 active signals (otherwise default to 0 disagreement) | |
| Fail-Safe Maximum | Treat missing signals as maximum disagreement or apply a default penalty multiplier to be conservative | |

**User's choice:** Impute as Neutral (0)

---

### Question 4: How should the disagreement score map to the risk sizing multiplier?
| Option | Description | Selected |
|--------|-------------|----------|
| Linear decay | multiplier = 1.0 - disagreement_score (maximum disagreement reduces the allowed position limit to 0) | ✓ |
| Exponential decay | multiplier = exp(-2.0 * disagreement_score) (exponentially penalizes higher disagreement, but never fully shuts off trading unless extreme) | |
| Threshold/Step decay | 1.0 if disagreement < 0.3; 0.5 if between 0.3 and 0.7; 0.0 if > 0.7 | |

**User's choice:** Linear decay (multiplier = 1.0 - disagreement_score)

---

## CPPI Drawdown Floor Definition

### Question 1: How should the CPPI drawdown floor be tracked?
| Option | Description | Selected |
|--------|-------------|----------|
| Trailing Peak Floor | The floor trailing-updates based on peak portfolio value (floor = Peak Value * (1 - max_drawdown_limit)), which directly protects against peak-to-trough drawdowns | ✓ |
| Fixed Floor | The floor is set relative to the initial portfolio value (floor = Initial Value * (1 - max_drawdown_limit)) and stays constant throughout the run | |
| Dynamic Dollar Floor | The floor is a raw dollar value provided in the state data (or defaults to a static percentage of current portfolio value) | |

**User's choice:** Trailing Peak Floor

---

### Question 2: How should the CPPI multiplier scale as portfolio value approaches the floor?
| Option | Description | Selected |
|--------|-------------|----------|
| Linear Cushion Scaling | multiplier = Cushion / (Max Drawdown Limit * Peak Value), capped at 1.0. (If current value is at the peak, cushion is max, multiplier is 1.0. As current value falls towards the floor, multiplier scales down linearly to 0.0) | ✓ |
| Leveraged CPPI Scaling | multiplier = M * (Cushion / Current Value), capped at 1.0. (Standard financial CPPI where M is a risk multiplier parameter, e.g., M=3. It allows higher leverage when far from the floor and shuts down quickly as we get closer) | |
| Step-down Scaling | 1.0 if cushion > 50% of max drawdown limit; 0.5 if between 10% and 50%; 0.0 if < 10% | |

**User's choice:** Linear Cushion Scaling

---

### Question 3: How should the maximum drawdown limit parameter be configured?
| Option | Description | Selected |
|--------|-------------|----------|
| Configurable via state | Check state metadata or data (e.g., `state["data"]["max_drawdown_limit"]`) first, with a fallback default (e.g., 0.20 or 20%) if not specified | ✓ |
| Hardcoded Default | Hardcode a static value (e.g., 20%) in `src/risk/drawdown_guardrail.py` to keep the code minimal and simple | |
| Command Line Configured | Read it exclusively from a CLI flag parsed in `src/backtester.py` and passed into the state dict | |

**User's choice:** Configurable via state

---

### Question 4: How should the peak portfolio value be persisted across execution steps?
| Option | Description | Selected |
|--------|-------------|----------|
| Persisted in Portfolio State | Read and update `state["data"]["portfolio"]["peak_value"]` dynamically during each execution step (simplest for both backtests and live graphs) | ✓ |
| Calculated from transaction logs | Compute the peak value dynamically on each run by scanning the backtest history or database logs | |
| Stateless (No Peak Persistence) | Only use the current portfolio cash/value as the peak (effectively resetting the floor on each step — not recommended as it doesn't protect against drawdowns) | |

**User's choice:** Persisted in Portfolio State

---

## Kelly Sizing Inputs

### Question 1: How should the Kelly helper obtain the win probability and win/loss ratio?
| Option | Description | Selected |
|--------|-------------|----------|
| Explicit parameters | Pass `win_probability` (p) and `win_loss_ratio` (b) directly as parameters to the helper, letting caller agents (like consensus or risk manager in later phases) extract them from the state data | ✓ |
| State-driven lookup | Have the helper inspect the state (e.g., `state["data"]["analyst_signals"]`) and calculate the win probability based on the proportion of bullish/bearish analysts | |
| Static defaults | Use hardcoded default inputs (e.g., p=0.55, b=2.0) inside the helper, making it purely a mathematical function with no caller input | |

**User's choice:** Explicit parameters

---

### Question 2: What fractional multiplier and absolute position cap should be implemented in the Kelly helper?
| Option | Description | Selected |
|--------|-------------|----------|
| Quarter Kelly with 25% Cap | Apply a fractional multiplier of 0.25 (Quarter Kelly) and cap the final allocation at 25% of total portfolio value (highly conservative, standard in risk management) | ✓ |
| Half Kelly with 50% Cap | Apply a fractional multiplier of 0.50 (Half Kelly) and cap the final allocation at 50% of total portfolio value | |
| Fully Configurable Parameters | Accept `fractional_multiplier` (default 0.25) and `max_cap` (default 0.25) as parameters in the function signature, allowing complete customization | |

**User's choice:** Quarter Kelly with 25% Cap (default parameters `fractional_multiplier: float = 0.25`, `max_cap: float = 0.25`)

---

### Question 3: How should the "disabled by default" constraint be implemented in the Kelly helper?
| Option | Description | Selected |
|--------|-------------|----------|
| Flag parameter | Add `enabled: bool = False` to the function signature. If `False`, return a multiplier of 1.0 (neutral, no scaling). This allows callers to opt-in explicitly | ✓ |
| State configuration check | Look for `state["metadata"].get("enable_kelly", False)` in the function itself (which makes the function dependent on the state structure) | |
| Separate opt-in wrapper | Keep the math function pure (always calculates Kelly), and have the calling agent decide whether to call it based on state flags | |

**User's choice:** Flag parameter (`enabled: bool = False`)

---

### Question 4: How should the Kelly helper handle a negative Kelly calculation result?
| Option | Description | Selected |
|--------|-------------|----------|
| Floor at 0.0 | Floor the resulting allocation at 0.0 (if the math yields a negative bet size, we do not trade that ticker; Kelly should not independently initiate opposite trades) | ✓ |
| Neutralize to 1.0 | Return 1.0 (no scaling adjustment) on negative Kelly, letting other risk limits handle it without a Kelly penalty | |
| Return negative | Return the negative value, indicating that if the direction is short, we bet that size (or invert the signal) | |

**User's choice:** Floor at 0.0

---

## Pydantic Schema Extensibility

### Question 1: How should the hybrid schemas handle extra JSON fields returned by LLMs?
| Option | Description | Selected |
|--------|-------------|----------|
| Ignore extra fields | Use default Pydantic behavior which ignores and drops extra fields silently, maintaining a clean validated object without throwing parsing errors | ✓ |
| Allow extra fields | Configure the models with `model_config = {"extra": "allow"}` so that extra fields returned by the LLM are preserved in the parsed model object | |
| Forbid/Strict validation | Configure the models with `model_config = {"extra": "forbid"}` to raise a validation error if any extra fields are present, forcing LLM outputs to match perfectly | |

**User's choice:** Ignore extra fields silently

---

### Question 2: What fields should be defined in the HybridDecisionTrace schema?
| Option | Description | Selected |
|--------|-------------|----------|
| Comprehensive Trace | Include ticker, timestamp, regime (RegimeClassification), selected analysts (list of IDs), debate (optional DebateOutput), guardrails (GuardrailOutput), final decision (MetaLabelOutput), and reasoning summary | ✓ |
| Minimal Trace | Include ticker, timestamp, action stance, and a raw JSON/Dict field `raw_trace` to hold all intermediate agent outputs without strict nested schemas | |
| Strict Complete Trace | Every single intermediate agent output must have its own strictly typed, non-optional field in the schema | |

**User's choice:** Comprehensive Trace

---

### Question 3: How should optional fields in Pydantic models be represented?
| Option | Description | Selected |
|--------|-------------|----------|
| Nullable with default None | Define using `FieldType | None = None` or `Optional[FieldType] = None` so they default to `None` if omitted from the input JSON | ✓ |
| Required but Nullable | Define as `Optional[FieldType]` (without a default value) so the input is required to explicitly contain the key, even if its value is `null`/`None` | |
| Default Empty Objects | Initialize optional schemas with their own default empty instances (e.g., `default_factory=DebateOutput` with all-nullable fields) to avoid None-checks in down-stream logic | |

**User's choice:** Nullable with default None

---

### Question 4: What JSON key casing should the Pydantic schemas enforce?
| Option | Description | Selected |
|--------|-------------|----------|
| Snake_case only | Keep schemas matching Python conventions (snake_case in both JSON and Python code) to avoid key-mapping overhead and maintain consistency with the CLI backtester | ✓ |
| CamelCase aliases | Use Pydantic's alias generator to serialize JSON keys to camelCase (e.g. `agentSelection`) while keeping Python attributes in snake_case (e.g. `agent_selection`) | |
| Configurable via model | Allow either by setting `populate_by_name=True` on aliases so both snake_case and camelCase are parsed successfully | |

**User's choice:** Snake_case only

---

## the agent's Discretion

Standard math calculations and tests details are deferred to the agent's implementation plan and planning phase.

## Deferred Ideas

None.
