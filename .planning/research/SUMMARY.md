# Project Research Summary

**Project:** AI Hedge Fund — Hybrid Decision Engine
**Domain:** Hybrid Research Decision Engine
**Researched:** 2026-06-09
**Confidence:** HIGH

## Executive Summary

The Hybrid Research Decision Engine upgrades the existing AI Hedge Fund's static analyst model to an adaptive, debate-driven, and risk-calibrated trading workflow. In this design, LLMs serve as analytical engines generating and challenging theses, while deterministic math and python guardrails own all trade admissibility and position sizing.

The core approach introduces a Psychological Guardrail and Safe Debate layer to address the uncalibrated nature of LLM signals and herding bias. By capturing decision traces in a reflection recorder, the system establishes a feedback loop for evaluating model accuracy against real financial outcomes without leaking future data.

## Key Findings

### Recommended Stack

The system remains anchored on Python 3.11, LangGraph, and FastAPI. Pydantic is introduced as the core validation tool to enforce strict type contracts for the new hybrid schemas (`src/schemas/hybrid.py`).

**Core technologies:**
- **Python 3.11 / Poetry**: Core runtime and package management.
- **LangGraph**: Workflow orchestration for agent selector, debate, and consensus stages.
- **Pydantic**: Model contract safety.

### Expected Features

**Must have (table stakes):**
- **Structured Schemas**: Shared models for regime, selection, debate, guardrails, and meta-labels.
- **Deterministic Sizing Hook**: Multipliers in Risk Manager and suppression logic in Portfolio Manager.
- **Calibrated Confidence**: Calibration using dispersion, disagreement, and subjectivity metrics.

**Should have (competitive):**
- **Safe Debate Layer**: Opposing long/short/critique perspectives to break confirmation bias.
- **Regime Classification**: Volatility and trend classification on pricing windows.
- **Adaptive Agent Selection**: Dynamic selector using `ANALYST_CONFIG`.

**Defer (v2+):**
- **Self-Calibration Engine**: Automated offline optimization of multipliers using reflection logs.

### Architecture Approach

The architecture compiles pricing and context to select agents, passes outputs through a safe debate layer, aggregates them in consensus and psychological guardrails, and feeds calibrated multipliers to deterministic risk and portfolio managers.

**Major components:**
1. **Regime Classifier & Agent Selector**: Custom LangGraph nodes mapping market status to active analysts.
2. **Safe Debate & Consensus**: sequential critique nodes synthesizing dominant and minority reports.
3. **Psychological Guardrail & Meta-Labeler**: Dampening layer calculating calibrated confidence and permissions.
4. **Risk & Portfolio Managers**: Execution gates enforcing deterministic constraints.

### Critical Pitfalls

1. **Unconstrained LLM Sizing**: Cured by computing `allowed_actions` and capping quantities in Python before final LLM choices.
2. **Future Leakage**: Solved by writing outcome data offline after the backtest iteration finishes.
3. **Herding Bias**: Addressed by calculating inter-agent disagreement and standard deviation to damp sizing limits.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Shared Hybrid Schemas
**Rationale:** Establishes type contract safety before writing any logic.
**Delivers:** `src/schemas/hybrid.py`.

### Phase 2: Deterministic Risk Utilities
**Rationale:** Creates pure mathematical helpers without LLM overhead.
**Delivers:** `src/risk/disagreement.py` and `drawdown_guardrail.py`.

### Phase 3: Psychological Guardrails
**Rationale:** Integrates confidence calibration prior to adding complex debate networks.
**Delivers:** `src/agents/psychological_guardrail.py`.

### Phase 4: Consensus & Basic Debate
**Rationale:** Establishes thesis aggregation. Consensus is built first, followed by sequential debate components.
**Delivers:** `src/agents/debate/consensus.py`, `bull_researcher.py`, `bear_researcher.py`, and `risk_red_team.py`.

### Phase 5: Meta-Labeler
**Rationale:** Bridges guardrail outputs with execution permissions.
**Delivers:** `src/agents/meta_labeler.py`.

### Phase 6-7: Risk & Portfolio Integration
**Rationale:** Hooks the calibrated multipliers and suppression labels into the deterministic gates.
**Delivers:** Updates to `src/agents/risk_manager.py` and `src/agents/portfolio_manager.py`.

### Phase 8: Adaptive GoA Selection
**Rationale:** Adds dynamic analyst routing using the regime classifier.
**Delivers:** `src/graph/regime_classifier.py` and `agent_selector.py`.

### Phase 9: Backtest Reflection Recorder
**Rationale:** Adds JSONL tracing to evaluate the final system.
**Delivers:** `src/reflection/recorder.py`.

### Research Flags

- **Phase 4 (Debate Layer):** Complex LLM prompt chains; needs careful output format validation to avoid crashes.
- **Phase 8 (Adaptive Selector):** Needs pricing window extraction logic; ensure pricing data is available inside LangGraph state.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing stack is mature; additions are standard libraries. |
| Features | HIGH | Directly maps to the hybrid decision engine spec. |
| Architecture | HIGH | Fits cleanly inside the existing LangGraph DAG layout. |
| Pitfalls | HIGH | Solves major failure modes observed in LLM trading setups. |

**Overall confidence:** HIGH

### Gaps to Address

- **Regime Data Ingestion**: We need to verify if the LangGraph state has access to the full pricing array during backtests to perform regime calculations. This will be addressed during Phase 8 planning.

## Sources

### Primary (HIGH confidence)
- [docs/hybrid-decision-engine/PRD.md](file:///c:/workspaces/ai-hedge-fund-forked/docs/hybrid-decision-engine/PRD.md)
- [docs/hybrid-decision-engine/module-contracts.md](file:///c:/workspaces/ai-hedge-fund-forked/docs/hybrid-decision-engine/module-contracts.md)

---
*Research completed: 2026-06-09*
*Ready for roadmap: yes*
