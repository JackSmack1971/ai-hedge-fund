# Requirements: AI Hedge Fund — Hybrid Decision Engine

**Defined:** 2026-06-09
**Core Value:** LLMs may reason, critique, and debate, but deterministic mathematical and risk controls must retain final authority over trading actions, position sizing, admissibility, and backtest accounting.

## v1 Requirements

### Schemas

- [ ] **SCHM-01**: Define structured Pydantic models for all hybrid decision metadata (`src/schemas/hybrid.py`), including `RegimeClassification`, `AgentSelection`, `ThesisOutput`, `DebateOutput`, `GuardrailOutput`, `MetaLabelOutput`, and `HybridDecisionTrace`.

### Risk Utilities

- [ ] **RISK-01**: Implement deterministic signal disagreement score and standard deviation dispersion functions in `src/risk/disagreement.py`.
- [ ] **RISK-02**: Implement CPPI drawdown multiplier calculations in `src/risk/drawdown_guardrail.py` that reduce exposure as portfolio value approaches floor.
- [ ] **RISK-03**: Implement optional fractional Kelly helper in `src/risk/sizing.py` capped and disabled by default.

### Psychological Guardrails

- [x] **PSY-01**: Implement `psychological_guardrail_agent` converting raw analyst signals into calibrated confidence, herding flags, and confidence multipliers.

### Debate & Consensus

- [x] **DEBT-01**: Implement `consensus_agent` summarizing dominant/minority reports, consensus confidence, and unresolved conflicts.
- [x] **DEBT-02**: Implement Safe Debate layer (Bull Researcher, Bear Researcher, Risk Red-Team sequential LLM agents) enabled via `debate_mode` flag.

### Meta-Labeler

- [x] **META-01**: Implement `meta_labeler_agent` mapping guardrail outputs to permission labels (`allow`, `reduce`, `suppress`, `hold_only`) and size multipliers.

### Execution Integration

- [ ] **INT-01**: Integrate risk manager (`src/agents/risk_manager.py`) to consume hybrid guardrails, meta-label sizing multipliers, and drawdown multipliers to scale position limits.
- [ ] **INT-02**: Integrate portfolio manager (`src/agents/portfolio_manager.py`) to enforce meta-label allowed actions (suppress/hold_only) and reduced quantities.

### Routing & Telemetry

- [ ] **ROUT-01**: Implement deterministic market regime classifier based on pricing, volatility, and trend metrics.
- [ ] **ROUT-02**: Implement adaptive Graph-of-Agents selection choosing relevant analysts dynamically based on regime.
- [ ] **ROUT-03**: Implement reflection recorder (`src/reflection/recorder.py`) storing JSONL traces during backtests with offline outcome evaluation.

## v2 Requirements

### Online Self-Calibration

- **CAL-01**: Implement automatic self-calibration system updating confidence multipliers online based on historical reflection logs.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Live Broker Trading | Purely for educational backtesting and research |
| RL Order Execution | High complexity, not needed for thesis testing |
| Automatic Prompt Modification | Avoid unstable runtime behavior |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCHM-01 | Phase 1 | Pending |
| RISK-01 | Phase 2 | Pending |
| RISK-02 | Phase 2 | Pending |
| RISK-03 | Phase 2 | Pending |
| PSY-01 | Phase 3 | Complete |
| DEBT-01 | Phase 4 | Complete |
| DEBT-02 | Phase 4 | Complete |
| META-01 | Phase 5 | Complete |
| INT-01 | Phase 6 | Pending |
| INT-02 | Phase 7 | Pending |
| ROUT-01 | Phase 8 | Pending |
| ROUT-02 | Phase 8 | Pending |
| ROUT-03 | Phase 9 | Pending |

**Coverage:**

- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-09*
*Last updated: 2026-06-09 after initial definition*
