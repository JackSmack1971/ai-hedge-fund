# Milestone v1.0 — Project Summary

**Generated:** 2026-06-08
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

An educational proof of concept for an AI-powered hedge fund and backtesting system. It compiles visual agent DAGs into LangGraph workflows, allowing LLM-based analyst agents to generate trading signals that are processed through risk management and portfolio management layers.

### Core Value
LLMs may reason, critique, debate, and analyze, but deterministic mathematical and risk controls must retain final authority over trading actions, position sizing, admissibility, and backtest accounting.

### Milestone Status
* **Current Milestone:** v1.0
* **Status:** Planning / In-progress (0 of 4 phases completed)
* **Current Focus:** Phase 1: Foundation & Schemas (Status: Ready to plan)

---

## 2. Architecture & Technical Decisions

The planned architecture transitions the hedge fund from static analyst calls to a dynamic, debate-driven, and risk-calibrated hybrid decision engine.

### Core Design Decisions:
- **Decision:** Numerical mapping for analyst stances (Buy = +1, Hold = 0, Sell = -1)
  - **Why:** Enables standard deviation and distance calculations across analyst recommendations.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Disagreement score as normalized standard deviation
  - **Why:** Maximum standard deviation represents a 50/50 split between Buy and Sell. Maps to a risk multiplier via linear decay (`multiplier = 1.0 - disagreement_score`).
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Impute missing or null analyst signals as Neutral (0)
  - **Why:** Ensures all selected analysts are represented in the standard deviation calculation rather than ignoring missing votes.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** CPPI drawdown floor using Trailing Peak Floor
  - **Why:** Protects against peak-to-trough drawdowns: `floor = Peak Value * (1 - max_drawdown_limit)`.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Linear Cushion Scaling for CPPI risk multiplier
  - **Why:** Scales down allowed position limits as current portfolio value approaches the floor. Capped at 1.0.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Explicit parameters for Kelly helper (`win_probability` and `win_loss_ratio`)
  - **Why:** Let caller agents handle state lookup and logic.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Quarter Kelly with 25% Cap
  - **Why:** Highly conservative position sizing helper, standard in risk management.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Enabled-flag for Kelly helper (`enabled: bool = False`)
  - **Why:** Kelly sizing helper is disabled by default, returning a neutral 1.0 multiplier unless explicitly enabled.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Floor Kelly result at 0.0
  - **Why:** Avoids negative allocations or short position triggers from Kelly calculation itself.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Ignore extra JSON fields silently in Pydantic schemas
  - **Why:** Avoids validation errors for unexpected LLM output fields.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Comprehensive trace schema (`HybridDecisionTrace`)
  - **Why:** Contains ticker, timestamp, regime, selected analysts, debate (optional), guardrails, final decision, and reasoning summary.
  - **Phase:** Phase 1: Foundation & Schemas
- **Decision:** Snake_case only for JSON keys
  - **Why:** Keeps schemas consistent with Python/CLI conventions without key-mapping overhead.
  - **Phase:** Phase 1: Foundation & Schemas

### Technology Stack
- **Core Runtime & Languages:** Python 3.11, Node.js 20.x, TypeScript 5.3, Poetry 1.7.1, npm 10.x
- **Frameworks & Orchestration:** FastAPI 0.104.0, LangGraph 0.3.0, LangChain 0.3.7, React 18.2, Vite 5.0.12
- **Testing & Verification:** Pytest 8.3, Pytest-Cov, Pytest-Asyncio

---

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
| 1 | Foundation & Schemas | Pending / Planning | Preserved baseline verification, shared hybrid schemas, and pure math risk utilities. |
| 2 | Hybrid Agents & Meta-Labeler | Planned / Not started | Calibrated confidence, consensus aggregation, debate layer, and meta-label permissions. |
| 3 | Sizing & Execution Integrations | Planned / Not started | Consume multipliers and suppressions in Risk and Portfolio Managers. |
| 4 | Adaptive Routing & Reflection | Planned / Not started | Dynamic analyst selector and JSONL trace recorder. |

---

## 4. Requirements Coverage

- [ ] **SCHM-01**: Define structured Pydantic models for all hybrid decision metadata (`src/schemas/hybrid.py`) - **Pending**
- [ ] **RISK-01**: Implement deterministic signal disagreement score and standard deviation dispersion functions in `src/risk/disagreement.py` - **Pending**
- [ ] **RISK-02**: Implement CPPI drawdown multiplier calculations in `src/risk/drawdown_guardrail.py` - **Pending**
- [ ] **RISK-03**: Implement optional fractional Kelly helper in `src/risk/sizing.py` - **Pending**
- [ ] **PSY-01**: Implement `psychological_guardrail_agent` for confidence calibration, subjectivity, and herding/dispersion - **Pending**
- [ ] **DEBT-01**: Implement `consensus_agent` summarizing reports, consensus confidence, and conflicts - **Pending**
- [ ] **DEBT-02**: Implement Safe Debate layer (Bull/Bear/Risk Red-Team sequential agents) - **Pending**
- [ ] **META-01**: Implement `meta_labeler_agent` mapping guardrails to permission labels - **Pending**
- [ ] **INT-01**: Integrate risk manager (`src/agents/risk_manager.py`) to consume multipliers and scale position limits - **Pending**
- [ ] **INT-02**: Integrate portfolio manager (`src/agents/portfolio_manager.py`) to respect allowed actions and quantities - **Pending**
- [ ] **ROUT-01**: Implement deterministic market regime classifier - **Pending**
- [ ] **ROUT-02**: Implement adaptive Graph-of-Agents selection choosing analysts dynamically based on regime - **Pending**
- [ ] **ROUT-03**: Implement reflection recorder (`src/reflection/recorder.py`) storing JSONL traces - **Pending**

---

## 5. Key Decisions Log

- **D-01:** Represent analyst recommendations numerically: Buy as +1, Hold/Neutral as 0, Sell as -1.
- **D-02:** Calculate the disagreement score as the normalized standard deviation of stances across analysts, where maximum standard deviation represents a 50/50 split between Buy and Sell. Sizing multiplier = 1.0 - disagreement_score.
- **D-03:** Handle missing or null analyst signals by imputing them as Hold/Neutral (0) in the standard deviation calculation.
- **D-04:** Track the CPPI drawdown floor dynamically using a Trailing Peak Floor model: `floor = Peak Value * (1 - max_drawdown_limit)`.
- **D-05:** Calculate the CPPI risk multiplier using Linear Cushion Scaling: `multiplier = Cushion / (Max Drawdown Limit * Peak Value)`, capped at 1.0.
- **D-06:** Keep the max drawdown limit configurable via state data, with a fallback default of 0.20 (20%).
- **D-07:** Persist the peak portfolio value dynamically in the portfolio state (`state['data']['portfolio']['peak_value']`) across execution steps.
- **D-08:** Pass `win_probability` (p) and `win_loss_ratio` (b) explicitly as parameters to the Kelly helper function.
- **D-09:** Scale the computed Kelly bet size to Quarter Kelly (0.25 multiplier) and enforce a strict cap of 25% of total portfolio value.
- **D-10:** Keep the Kelly sizing helper disabled by default via an `enabled: bool = False` argument.
- **D-11:** Floor the resulting Kelly allocation at 0.0.
- **D-12:** Ignore and drop extra JSON fields silently when parsing model inputs, avoiding validation errors for unexpected LLM output fields.
- **D-13:** Define `HybridDecisionTrace` containing ticker, timestamp, regime, selected analysts, debate, guardrails, final decision, and reasoning.
- **D-14:** Represent optional fields as nullable with default None (e.g. `FieldType | None = None`).
- **D-15:** Keep all JSON key casing as snake_case only.

---

## 6. Tech Debt & Deferred Items

### Codebase Tech Debt & Concerns
- **Dual Database Table Initialization:** Backend uses both direct `Base.metadata.create_all(bind=engine)` at startup and Alembic migrations, which can mask out-of-sync migrations and create schema drift.
- **Unresolved Linting Violations (Flake8):** ~687 unresolved flake8 violations are present, forcing CI to run with `continue-on-error: true`.
- **Non-Strict Type Checking (Mypy):** Mypy is configured in non-strict mode (`strict = false`) and type check failures are ignored.
- **Database Encryption Key Management:** Symmetric encryption relies on `DATABASE_ENCRYPTION_KEY`. If lost, saved API keys are unrecoverable.
- **SQLite Concurrency Limits:** SQLite's write locking can lead to `database is locked` under high concurrent execution.
- **Suffix-Based Node ID Mapping:** Visual graphs use custom React Flow IDs containing a 6-character alphanumeric suffix (e.g., `warren_buffett_abc123`). The backend parses these using string-splitting/suffix-stripping, which is fragile.
- **Financial Datasets API Free Tier:** Restricted to AAPL, GOOGL, MSFT, NVDA, and TSLA. Other stock tickers return empty responses.
- **Celery/Redis Package Approval Dependency:** Production asynchronous execution via Celery workers is currently blocked pending package license/review approval.

### Deferred Items
- *None.*

---

## 7. Getting Started

### Entry Points for New Contributors
1. **Run the Project CLI:**
   - Execute the main CLI workflow: `poetry run python src/main.py --ticker AAPL,MSFT,NVDA`
2. **Run a Historical Backtest:**
   - Run a backtest from the terminal: `poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA`
3. **Run the Test Suite:**
   - Run the tests: `poetry run pytest`

### Key Directories
- `src/` — Core analyst agents, backtesting logic, CLI entry points.
- `app/` — FastAPI backend and Vite/React/Tailwind frontend.
- `tests/` — pytest suite.

### Where to Look First
- `src/graph/state.py` — Represents the AgentState flowing between graph nodes.
- `src/agents/` — Base implementations of analyst agents.
- `.planning/` — Roadmap, project requirements, and phase designs.

---

## Stats

- **Timeline:** 2026-06-08 23:15:36 → 2026-06-08 23:27:50 (duration: ~12 minutes)
- **Phases:** 0 complete / 4 total
- **Commits:** 7
- **Files changed:** 15 (+1641 / -0)
- **Contributors:** Test User
