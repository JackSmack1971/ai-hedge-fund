# AI Hedge Fund — Hybrid Decision Engine

## What This Is

An educational proof of concept for an AI-powered hedge fund and backtesting system. It compiles visual agent DAGs into LangGraph workflows, allowing LLM-based analyst agents to generate trading signals that are processed through risk management and portfolio management layers.

## Core Value

LLMs may reason, critique, debate, and analyze, but deterministic mathematical and risk controls must retain final authority over trading actions, position sizing, admissibility, and backtest accounting.

## Requirements

### Validated

- ✓ **FLOW-COMP**: Compiler to translate React Flow JSON layouts to executable LangGraph workflows.
- ✓ **ANALYST-REG**: Central registry of 18 analyst agents with specialized investment styles.
- ✓ **DET-RISK**: Volatility-adjusted and correlation-adjusted position limits computed deterministically.
- ✓ **DET-PORTFOLIO**: Deterministic portfolio management constraints restricting allowed actions and max quantities.
- ✓ **BACKTEST-LOOP**: Historical backtesting engine that simulates daily trading decisions, cache warming, and performance metrics.
- ✓ **WEB-APP**: FastAPI backend with SSE streaming and React Flow UI for local run orchestration.

### Active

- [ ] **HYB-SCHEMAS**: Define structured Pydantic models for all hybrid decision metadata (`src/schemas/hybrid.py`).
- [ ] **DET-GUARDRAILS**: Implement deterministic risk/disagreement utilities, CPPI drawdown multiplier, and Kelly helper.
- [ ] **PSY-GUARDRAILS**: Add psychological guardrails agent for confidence calibration, subjectivity assessment, and herding/dispersion penalties.
- [ ] **CONSENSUS**: Implement consensus synthesis to aggregate analyst theses, minority reports, and conflict logs.
- [ ] **SAFE-DEBATE**: Create a debate layer (Bull/Bear/Red-Team agents) for rigorous thesis confrontation.
- [ ] **META-LABELER**: Build a trade admissibility filter that maps calibrated confidence and disagreement to trade permissions (`allow`, `reduce`, `suppress`, `hold_only`).
- [ ] **RISK-INTEGRATION**: Connect the risk manager to consume hybrid guardrails, meta-label sizing multipliers, and drawdown multipliers.
- [ ] **PORTFOLIO-INTEGRATION**: Constrain the portfolio manager to respect meta-label suppressions and quantity reductions.
- [ ] **ADAPTIVE-GOA**: Implement adaptive Graph-of-Agents selection based on market regime classification.
- [ ] **REFLECTION-REC**: Add structured JSONL decision trace recording during backtesting for evaluation and attribution.
- [ ] **EVAL-METRICS**: Add hybrid evaluation metrics comparing baseline versus hybrid runs.

### Out of Scope

- **LIVE-TRADING** — Real-money or broker-integrated execution, as this is purely for educational research.
- **RL-EXECUTION** — Reinforcement learning execution engines.
- **BLOOMBERG-INGESTION** — Direct institutional data feed ingestion.
- **PROMPT-AUTO-EVOLVE** — Automatic LLM self-modifying prompts from reflection records.

## Context

The current system supports static agent compilation where all selected analyst agents run in parallel and report to the risk manager and portfolio manager. There is no critique, consensus synthesis, herding detection, or structured attribution log, making the agent signals uncalibrated and prone to confirmation bias.

## Constraints

- **Tech Stack**: Must use Python 3.11, Poetry, LangGraph, LangChain, and SQLite.
- **Security**: Database encryption key management via Fernet must be robustly handled.
- **Compatibility**: The system must run in baseline mode unless hybrid features are explicitly enabled via flags.
- **Licensing**: Celery worker integration is blocked pending package license approval.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid Design | LLMs generate/critique theses; deterministic math rules sizing and admissibility. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-09 after initialization*
