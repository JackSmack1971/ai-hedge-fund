# Plan 04-01 Summary: Regime Classifier and Adaptive Selector

**Completed:** 2026-06-09
**Status:** PASSED — 18 tests green, 575 total, zero regressions

## What Was Built

### src/regime/classifier.py (new)
- `classify_regime(prices_df) -> RegimeClassification` — pure deterministic function
- Calculates annualized volatility, short/long MA trend ratio, and price deviation from mean
- Priority evaluation: high_volatility → low_volatility → momentum → risk_off → valuation_stress → mean_reversion → risk_on (default)
- All thresholds are fixed constants (no LLM, fully reproducible)
- NaN/Inf guard via `_safe_float` helper
- Returns `RegimeClassification` from `src/schemas/hybrid.py`

### src/regime/selector.py (new)
- `select_analysts_for_regime(regime, available, min_analysts=3) -> list[str]`
- Maps regime labels to preferred analyst sets via `_REGIME_ANALYST_MAP`
- Guarantees `min_analysts` returned (fills from remaining if preferred subset too small)
- `risk_on` and `unknown` → no restriction (all analysts returned)
- Falls back to all available if no match at all

### src/main.py — adaptive routing (modified)
- Added `adaptive_mode: bool = False` parameter to `run_hedge_fund`
- Added `_apply_adaptive_routing(tickers, start_date, end_date, selected_analysts)` helper:
  - Fetches prices per ticker via existing `get_prices` / `prices_to_df`
  - Classifies regime per ticker using `classify_regime`
  - Votes plurality regime across tickers
  - Calls `select_analysts_for_regime` to filter analyst list
  - Returns `(effective_analysts, regime_classification_by_ticker, regime_selection_by_ticker)`
- When `adaptive_mode=False`: skips all above, behavior unchanged from baseline
- `regime_classification` and `regime_selection` dicts injected into `state["data"]` for reflection recorder

## Decisions Implemented
ROUT-01 (classifier), ROUT-02 (selector)

## Verification
- `pytest tests/test_regime_classifier.py tests/test_adaptive_selector.py -v --no-cov`: 18/18 PASSED
- `pytest tests/ --no-cov -q`: 575 passed, 0 failed
