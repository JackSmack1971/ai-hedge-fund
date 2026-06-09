---
plan: 01-02
phase: 01-foundation-schemas
status: complete
completed: 2026-06-09
key-files:
  created:
    - src/risk/__init__.py
    - src/risk/disagreement.py
    - src/risk/drawdown_guardrail.py
    - src/risk/sizing.py
    - tests/risk/__init__.py
    - tests/risk/test_disagreement.py
    - tests/risk/test_drawdown_guardrail.py
    - tests/risk/test_sizing.py
---

## Summary

Created `src/risk/` package with three pure-math stdlib-only modules satisfying RISK-01, RISK-02, RISK-03.

**disagreement.py (RISK-01):** `compute_disagreement_score` returns population std dev of stances [0,1]; None imputed as 0. `compute_disagreement_multiplier` returns 1.0 - score. Tested: unanimous=0.0, 50/50=-1.0, full range property.

**drawdown_guardrail.py (RISK-02):** `compute_cppi_floor` = peak*(1-limit). `compute_cppi_multiplier` = cushion/(limit*peak), clamped [0,1]; returns 1.0 when no peak. Stateless — peak tracked by caller per D-07.

**sizing.py (RISK-03):** `fractional_kelly` returns 1.0 when disabled (neutral, not zero). Quarter Kelly (0.25x) capped at 0.25, floored at 0.0 per D-09/D-10/D-11.

**Verification:** 42 risk tests pass. Full suite: 464 passed, 0 failed (417 baseline + 47 new).

## Self-Check: PASSED
