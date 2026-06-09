# Roadmap: AI Hedge Fund — Hybrid Decision Engine

## Overview

Upgrades the static analyst model of the AI Hedge Fund into an adaptive, debate-driven, and risk-calibrated research engine. It builds schemas, pure mathematical risk utilities, psychological guardrail/consensus/debate agents, and meta-labelers, integrating them into the existing deterministic risk and portfolio manager gates. Finally, it implements adaptive routing based on market regime and reflection logs.

## Phases

- [x] **Phase 1: Foundation & Schemas** - Preserved baseline verification, shared hybrid schemas, and pure math risk utilities.
- [ ] **Phase 2: Hybrid Agents & Meta-Labeler** - Calibrated confidence, consensus aggregation, debate layer, and meta-label permissions.
- [ ] **Phase 3: Sizing & Execution Integrations** - Consume multipliers and suppressions in Risk and Portfolio Managers.
- [ ] **Phase 4: Adaptive Routing & Reflection** - Dynamic analyst selector and JSONL trace recorder.

## Phase Details

### Phase 1: Foundation & Schemas
**Goal**: Preserved baseline verification, shared hybrid schemas, and pure math risk utilities.
**Mode**: mvp
**Depends on**: Nothing (first phase)
**Requirements**: SCHM-01, RISK-01, RISK-02, RISK-03
**Success Criteria**:
  1. The existing CLI and backtester execute without regression when hybrid mode is disabled.
  2. All hybrid Pydantic models in `src/schemas/hybrid.py` import and serialize to JSON.
  3. Deterministic disagreement and drawdown formulas calculate correct multipliers under test.
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Patch src/schemas/hybrid.py: ConfigDict(extra="ignore") on all 7 models, add timestamp and reasoning_summary to HybridDecisionTrace, add D-12/D-13 test coverage
- [x] 01-02-PLAN.md — Create src/risk package: disagreement score (RISK-01), CPPI drawdown multiplier (RISK-02), fractional Kelly helper (RISK-03) with full test coverage

### Phase 2: Hybrid Agents & Meta-Labeler
**Goal**: Calibrated confidence, consensus aggregation, debate layer, and meta-label permissions.
**Mode**: mvp
**Depends on**: Phase 1
**Requirements**: PSY-01, DEBT-01, DEBT-02, META-01
**Success Criteria**:
  1. The psychological guardrail calibrates raw confidence based on dispersion and herding.
  2. The consensus agent aggregates opposing stances into a structured output.
  3. The debate layer runs sequential bull/bear/red-team agents under the `debate_mode` flag.
  4. The meta-labeler assigns correct permission labels and sizing scalars.
**Plans**: 2 plans

Plans:
- [ ] 02-01: Psychological Guardrail and Consensus agents implementation.
- [ ] 02-02: Safe Debate and Meta-Labeler implementation.

### Phase 3: Sizing & Execution Integrations
**Goal**: Consume multipliers and suppressions in Risk and Portfolio Managers.
**Mode**: mvp
**Depends on**: Phase 2
**Requirements**: INT-01, INT-02
**Success Criteria**:
  1. Risk Manager applies disagreement, CPPI, and meta-label multipliers to remaining limits.
  2. Portfolio Manager constrains allowed actions and quantities based on meta-labels.
  3. The end-to-end flow runs successfully with hybrid mode enabled.
**Plans**: 2 plans

Plans:
- [ ] 03-01: Risk Manager multiplier integration.
- [ ] 03-02: Portfolio Manager action suppression integration.

### Phase 4: Adaptive Routing & Reflection
**Goal**: Dynamic analyst selector and JSONL trace recorder.
**Mode**: mvp
**Depends on**: Phase 3
**Requirements**: ROUT-01, ROUT-02, ROUT-03
**Success Criteria**:
  1. Regime classifier determines volatility/trend states deterministically.
  2. Selector chooses relevant analysts dynamically per ticker based on regime.
  3. Reflection recorder logs full decision traces to JSONL for evaluation.
**Plans**: 2 plans

Plans:
- [ ] 04-01: Regime Classifier and Adaptive Selector.
- [ ] 04-02: Backtest Reflection Recorder and Metrics.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Schemas | 2/2 | Complete | 2026-06-09 |
| 2. Hybrid Agents & Meta-Labeler | 0/2 | Not started | - |
| 3. Sizing & Execution Integrations | 0/2 | Not started | - |
| 4. Adaptive Routing & Reflection | 0/2 | Not started | - |
