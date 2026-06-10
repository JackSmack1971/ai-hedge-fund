"""Deterministic market regime classifier (ROUT-01).

Classifies market regime from price data using pure math — no LLM calls.
Thresholds are fixed constants; output is fully reproducible for a given prices_df.
"""

import math

import numpy as np
import pandas as pd

from src.schemas.hybrid import RegimeClassification

# Regime classification thresholds
_HIGH_VOL_THRESHOLD = 0.40       # annualized vol > 40% → high_volatility
_LOW_VOL_THRESHOLD = 0.12        # annualized vol < 12% → low_volatility
_MOMENTUM_THRESHOLD = 0.05       # short MA > long MA by 5% → momentum
_RISK_OFF_THRESHOLD = -0.05      # short MA < long MA by 5% → risk_off
_MEAN_REV_UPPER = 0.08           # price > 8% above mean → valuation_stress
_MEAN_REV_LOWER = -0.08          # price < 8% below mean → mean_reversion

_SHORT_WINDOW = 10
_LONG_WINDOW = 20
_MIN_DATA_POINTS = 5


def classify_regime(prices_df: pd.DataFrame) -> RegimeClassification:
    """Classify market regime from OHLCV price data deterministically.

    Evaluation order: high_volatility → low_volatility → momentum → risk_off
    → valuation_stress → mean_reversion → risk_on (default).
    """
    if prices_df.empty or len(prices_df) < _MIN_DATA_POINTS:
        return RegimeClassification(
            regime="unknown",
            confidence=0,
            reasoning=f"Insufficient data: {len(prices_df)} rows (minimum {_MIN_DATA_POINTS})",
        )

    closes = prices_df["close"].dropna()
    if len(closes) < _MIN_DATA_POINTS:
        return RegimeClassification(
            regime="unknown", confidence=0, reasoning="Insufficient non-null close prices"
        )

    returns = closes.pct_change().dropna()
    if len(returns) < 2:
        return RegimeClassification(
            regime="unknown", confidence=0, reasoning="Insufficient return data"
        )

    annualized_vol = _safe_float(returns.std() * math.sqrt(252), default=0.25)
    short_w = min(_SHORT_WINDOW, len(closes) // 2 or 1)
    long_w = min(_LONG_WINDOW, len(closes))
    short_ma = float(closes.tail(short_w).mean())
    long_ma = float(closes.tail(long_w).mean())
    trend_ratio = (short_ma / long_ma - 1.0) if long_ma > 0 else 0.0
    current = float(closes.iloc[-1])
    dev_from_mean = (current / long_ma - 1.0) if long_ma > 0 else 0.0

    if annualized_vol > _HIGH_VOL_THRESHOLD:
        excess = annualized_vol - _HIGH_VOL_THRESHOLD
        confidence = min(100, int(70 + excess * 100))
        return RegimeClassification(
            regime="high_volatility",
            confidence=confidence,
            reasoning=f"Annualized volatility {annualized_vol:.1%} exceeds {_HIGH_VOL_THRESHOLD:.0%} threshold",
        )

    if annualized_vol < _LOW_VOL_THRESHOLD:
        margin = _LOW_VOL_THRESHOLD - annualized_vol
        confidence = min(100, int(70 + margin * 200))
        return RegimeClassification(
            regime="low_volatility",
            confidence=confidence,
            reasoning=f"Annualized volatility {annualized_vol:.1%} below {_LOW_VOL_THRESHOLD:.0%} threshold",
        )

    if trend_ratio > _MOMENTUM_THRESHOLD:
        confidence = min(100, int(60 + trend_ratio * 200))
        return RegimeClassification(
            regime="momentum",
            confidence=confidence,
            reasoning=f"Short MA ({short_w}d) is {trend_ratio:.1%} above long MA ({long_w}d)",
        )

    if trend_ratio < _RISK_OFF_THRESHOLD:
        confidence = min(100, int(60 + abs(trend_ratio) * 200))
        return RegimeClassification(
            regime="risk_off",
            confidence=confidence,
            reasoning=f"Short MA ({short_w}d) is {abs(trend_ratio):.1%} below long MA ({long_w}d)",
        )

    if dev_from_mean > _MEAN_REV_UPPER:
        confidence = min(100, int(55 + dev_from_mean * 100))
        return RegimeClassification(
            regime="valuation_stress",
            confidence=confidence,
            reasoning=f"Price {dev_from_mean:.1%} above {long_w}-period mean (overextended)",
        )

    if dev_from_mean < _MEAN_REV_LOWER:
        confidence = min(100, int(55 + abs(dev_from_mean) * 100))
        return RegimeClassification(
            regime="mean_reversion",
            confidence=confidence,
            reasoning=f"Price {abs(dev_from_mean):.1%} below {long_w}-period mean (depressed)",
        )

    confidence = max(40, min(70, int(50 + (1.0 - annualized_vol / _HIGH_VOL_THRESHOLD) * 20)))
    return RegimeClassification(
        regime="risk_on",
        confidence=confidence,
        reasoning=(
            f"Moderate vol {annualized_vol:.1%}, trend {trend_ratio:+.1%}, "
            f"price {dev_from_mean:+.1%} vs mean — no strong regime signal"
        ),
    )


def _safe_float(value: float, default: float = 0.0) -> float:
    """Return default if value is NaN or Inf."""
    try:
        v = float(value)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default
