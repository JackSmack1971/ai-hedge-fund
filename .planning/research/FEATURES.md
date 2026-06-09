# Feature Research

**Domain:** Hybrid Research Decision Engine for AI Hedge Fund
**Researched:** 2026-06-09
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Central Schemas | Validation and serialization of hybrid traces | LOW | Standard models in `src/schemas/hybrid.py`. |
| Deterministic Risk Utilities | Math-based disagreement and drawdown constraints | LOW | Coded in vanilla Python (`src/risk/`). No LLM calls. |
| Consensus Synthesis | Clean aggregation of analyst outputs | MEDIUM | Preserves dominant and minority theses. |
| Risk & Portfolio Hook | Sizing adjustments using hybrid multipliers | MEDIUM | Existing code must consume hybrid dict values safely. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Safe Debate Layer | Proactively challenges confirmation bias with opposing LLM stances | HIGH | Spawns Bull, Bear, and Red-Team agents in sequence. |
| Psychological Guardrail | Empirically dampens overconfidence and herding | MEDIUM | Computes dispersion, subjectivity, herding, and calibration. |
| Meta-Labeler | Rules-based trade admissibility filter | MEDIUM | Returns `allow`, `reduce`, `suppress`, `hold_only`. |
| Adaptive GoA Selection | Selects analysts dynamically based on market regime | HIGH | Uses regime classifier and centrale analyst configs. |
| Backtest Reflection | Creates a persistent trace of reasoning vs. outcomes | MEDIUM | JSONL trace for evaluation and future calibration. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| LLM Order Execution | Let LLM specify final trading quantities | Uncalibrated LLMs will buy too much or ignore margin | Deterministic sizing limits inside Portfolio Manager |
| Auto-tuning Prompt Loops | Dynamic prompt adjustment based on same-day outcomes | Prone to overfitting and future leakage | Offline evaluation of reflection records |

## Feature Dependencies

```
[Shared Schemas]
    └──requires──> [Deterministic Risk Utilities]
                       └──requires──> [Psychological Guardrails]
                                          └──requires──> [Meta-Labeler]
                                                             └──requires──> [Risk & Portfolio Hook]
[Safe Debate] ──enhances──> [Consensus Synthesis]
[Regime Classifier] ──requires──> [Adaptive GoA Selection]
[Backtest Reflection] ──requires──> [Evaluation Metrics]
```

### Dependency Notes

- **Psychological Guardrails requires Deterministic Risk Utilities:** Calibration and multipliers rely on the disagreement and dispersion formulas.
- **Meta-Labeler requires Psychological Guardrails:** Admissibility labels depend on the calibrated confidence output.
- **Safe Debate enhances Consensus:** Feeding debate arguments into consensus results in richer theses and conflict summaries.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] **Shared Schemas** — `src/schemas/hybrid.py`
- [ ] **Deterministic Risk Utilities** — Disagreement and CPPI drawdown multipliers.
- [ ] **Psychological Guardrails Agent** — Confidence calibration and risk flags.
- [ ] **Consensus Agent** — Aggregating analyst signals and theses.
- [ ] **Meta-Labeler** — Sizing and admissibility labels.
- [ ] **Risk Manager Integration** — Consume multipliers to reduce position limits.
- [ ] **Portfolio Manager Integration** — Enforce suppressions and allowed actions.

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] **Adaptive GoA Selection** — Dynamic selector based on regime classification.
- [ ] **Safe Debate Layer** — Bull, Bear, and Red-Team agents.
- [ ] **Reflection Recorder** — JSONL trace capture during backtesting.

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Self-Calibration Engine** — Automatic optimization of confidence multipliers using reflection history.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Shared Schemas | HIGH | LOW | P1 |
| Deterministic Risk Utilities | HIGH | LOW | P1 |
| Psychological Guardrails | HIGH | MEDIUM | P1 |
| Consensus Agent | HIGH | MEDIUM | P1 |
| Meta-Labeler | HIGH | MEDIUM | P1 |
| Risk & Portfolio Integration | HIGH | HIGH | P1 |
| Adaptive GoA Selection | MEDIUM | HIGH | P2 |
| Safe Debate Layer | HIGH | HIGH | P2 |
| Reflection Recorder | MEDIUM | MEDIUM | P2 |
| Evaluation Metrics | MEDIUM | LOW | P2 |

## Competitor Feature Analysis

| Feature | Static LLM Portfolio | Institutional Hedge Fund | Our Approach |
|---------|----------------------|--------------------------|--------------|
| Sizing | LLM outputs quantity | Deterministic risk models | LLM proposes thesis, deterministic code bounds size |
| Conflict | None (takes average) | Multi-person committee | LLM Debate + Psychological Guardrails herding penalty |

## Sources

- [docs/hybrid-decision-engine/PRD.md](file:///c:/workspaces/ai-hedge-fund-forked/docs/hybrid-decision-engine/PRD.md)
- [docs/hybrid-decision-engine/implementation-roadmap.md](file:///c:/workspaces/ai-hedge-fund-forked/docs/hybrid-decision-engine/implementation-roadmap.md)

---
*Feature research for: Hybrid Research Decision Engine*
*Researched: 2026-06-09*
