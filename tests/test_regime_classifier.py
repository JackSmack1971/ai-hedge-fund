"""ROUT-01 tests: deterministic market regime classifier."""

import math

import numpy as np
import pandas as pd
import pytest

from src.regime.classifier import classify_regime
from src.schemas.hybrid import RegimeClassification


def _make_prices(closes: list[float]) -> pd.DataFrame:
    """Build a minimal prices DataFrame from a list of close prices."""
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="B")
    return pd.DataFrame({"close": closes}, index=dates)


def _flat_prices(n: int = 30, base: float = 100.0) -> pd.DataFrame:
    """Flat prices → low volatility, neutral trend."""
    return _make_prices([base + i * 0.01 for i in range(n)])


def _high_vol_prices(n: int = 30) -> pd.DataFrame:
    """Alternating high-vol prices."""
    rng = np.random.default_rng(42)
    closes = [100.0]
    for _ in range(n - 1):
        closes.append(max(1.0, closes[-1] * (1 + rng.normal(0, 0.035))))
    return _make_prices(closes)


def _trending_up_prices(n: int = 30, step: float = 2.0) -> pd.DataFrame:
    """Steady upward trend → momentum regime."""
    return _make_prices([100.0 + i * step for i in range(n)])


def _trending_down_prices(n: int = 30, step: float = 2.0) -> pd.DataFrame:
    """Steady downward trend → risk_off regime."""
    return _make_prices([200.0 - i * step for i in range(n)])


def _trending_up_with_noise(n: int = 40) -> pd.DataFrame:
    """Strong upward trend with realistic noise — vol above low_vol threshold."""
    rng = np.random.default_rng(42)
    closes = [100.0]
    for _ in range(n - 1):
        r = 0.009 + rng.normal(0, 0.018)  # annualized vol ≈ 0.018*sqrt(252) ≈ 29%
        closes.append(max(1.0, closes[-1] * (1 + r)))
    return _make_prices(closes)


def _trending_down_with_noise(n: int = 40) -> pd.DataFrame:
    """Strong downward trend with realistic noise — vol above low_vol threshold."""
    rng = np.random.default_rng(7)
    closes = [200.0]
    for _ in range(n - 1):
        r = -0.009 + rng.normal(0, 0.018)
        closes.append(max(1.0, closes[-1] * (1 + r)))
    return _make_prices(closes)


# ---------------------------------------------------------------------------
# Basic structural tests
# ---------------------------------------------------------------------------

class TestClassifyRegimeStructure:
    def test_returns_regime_classification_instance(self):
        df = _flat_prices()
        result = classify_regime(df)
        assert isinstance(result, RegimeClassification)

    def test_empty_df_returns_unknown(self):
        result = classify_regime(pd.DataFrame())
        assert result.regime == "unknown"
        assert result.confidence == 0

    def test_too_few_rows_returns_unknown(self):
        result = classify_regime(_make_prices([100.0, 101.0]))
        assert result.regime == "unknown"

    def test_regime_is_valid_literal(self):
        valid = {
            "risk_on", "risk_off", "high_volatility", "low_volatility",
            "momentum", "mean_reversion", "news_shock", "valuation_stress", "unknown",
        }
        df = _flat_prices()
        result = classify_regime(df)
        assert result.regime in valid

    def test_confidence_in_range(self):
        for prices_fn in [_flat_prices, _trending_up_prices, _trending_down_prices]:
            result = classify_regime(prices_fn())
            assert 0 <= result.confidence <= 100

    def test_reasoning_is_nonempty_string(self):
        result = classify_regime(_flat_prices())
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0


# ---------------------------------------------------------------------------
# Regime detection tests
# ---------------------------------------------------------------------------

class TestRegimeDetection:
    def test_flat_low_vol_classified(self):
        """Very flat prices → low_volatility."""
        df = _make_prices([100.0 + i * 0.001 for i in range(40)])
        result = classify_regime(df)
        assert result.regime == "low_volatility"

    def test_uptrend_classified_as_momentum(self):
        """Strong upward trend with realistic noise → momentum."""
        df = _trending_up_with_noise()
        result = classify_regime(df)
        assert result.regime == "momentum"

    def test_downtrend_classified_as_risk_off(self):
        """Strong downward trend with realistic noise → risk_off."""
        df = _trending_down_with_noise()
        result = classify_regime(df)
        assert result.regime == "risk_off"

    def test_deterministic_same_input_same_output(self):
        """Same input always produces the same regime."""
        df = _flat_prices(n=30)
        result1 = classify_regime(df)
        result2 = classify_regime(df)
        assert result1.regime == result2.regime
        assert result1.confidence == result2.confidence

    def test_no_nan_in_output(self):
        """Result fields never contain NaN."""
        df = _trending_up_prices()
        result = classify_regime(df)
        assert not math.isnan(result.confidence)
        assert result.regime is not None

    def test_high_volatility_detected(self):
        """Prices with very high std dev → high_volatility."""
        rng = np.random.default_rng(0)
        closes = [100.0]
        for _ in range(29):
            closes.append(max(1.0, closes[-1] * (1 + rng.normal(0, 0.055))))
        df = _make_prices(closes)
        result = classify_regime(df)
        assert result.regime == "high_volatility"
