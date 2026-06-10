"""Adaptive analyst selector based on market regime (ROUT-02).

Maps regime classifications to preferred analyst subsets deterministically.
Falls back to all available analysts for unknown or unmapped regimes.
"""

from typing import Sequence

# Maps regime labels to sets of preferred analyst keys (from ANALYST_CONFIG).
# None means "use all analysts" — no restriction.
_REGIME_ANALYST_MAP: dict[str, set[str] | None] = {
    "high_volatility": {
        "technicals",
        "sentiment",
        "news_sentiment",
        "bill_ackman",
    },
    "low_volatility": {
        "warren_buffett",
        "charlie_munger",
        "ben_graham",
        "fundamentals",
        "valuation",
        "stanley_druckenmiller",
        "peter_lynch",
    },
    "momentum": {
        "technicals",
        "cathie_wood",
        "sentiment",
        "news_sentiment",
        "stanley_druckenmiller",
    },
    "risk_off": {
        "ben_graham",
        "warren_buffett",
        "valuation",
        "fundamentals",
        "aswath_damodaran",
    },
    "mean_reversion": {
        "technicals",
        "valuation",
        "fundamentals",
        "aswath_damodaran",
    },
    "valuation_stress": {
        "valuation",
        "fundamentals",
        "warren_buffett",
        "ben_graham",
        "aswath_damodaran",
    },
    "risk_on": None,      # no restriction — all analysts
    "news_shock": {
        "news_sentiment",
        "sentiment",
        "technicals",
        "bill_ackman",
    },
    "unknown": None,      # no restriction — all analysts
}

_DEFAULT_MIN_ANALYSTS = 3


def select_analysts_for_regime(
    regime: str,
    available_analysts: Sequence[str],
    min_analysts: int = _DEFAULT_MIN_ANALYSTS,
) -> list[str]:
    """Return subset of available_analysts preferred for the given regime.

    Guarantees at least min_analysts are returned when possible.
    If regime maps to None (risk_on, unknown) or preferred set intersects too few
    available analysts, falls back to the full available list.

    Args:
        regime: Regime label string (must match RegimeClassification.regime literal).
        available_analysts: All analyst keys available in the current workflow.
        min_analysts: Minimum number of analysts to return. Defaults to 3.

    Returns:
        Ordered list of analyst keys, preserving original ordering.
    """
    preferred = _REGIME_ANALYST_MAP.get(regime)
    if preferred is None:
        return list(available_analysts)

    selected = [a for a in available_analysts if a in preferred]

    if len(selected) < min_analysts:
        remaining = [a for a in available_analysts if a not in preferred]
        fill_count = max(0, min_analysts - len(selected))
        selected = selected + remaining[:fill_count]

    if not selected:
        return list(available_analysts)

    return selected
