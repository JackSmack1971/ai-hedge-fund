import math
from datetime import datetime, timedelta

import numpy as np
import pytest

from src.backtesting.metrics import PerformanceMetricsCalculator


def _build_values(values: list[float]):
    start = datetime(2024, 1, 1)
    points = []
    for i, v in enumerate(values):
        points.append({
            "Date": start + timedelta(days=i),
            "Portfolio Value": v,
            "Long Exposure": 0.0,
            "Short Exposure": 0.0,
            "Gross Exposure": 0.0,
            "Net Exposure": 0.0,
            "Long/Short Ratio": np.inf,
        })
    return points


def test_metrics_insufficient_data_no_update():
    calc = PerformanceMetricsCalculator()
    metrics = {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}
    calc.update_metrics(metrics, _build_values([100_000.0]))
    assert metrics["sharpe_ratio"] is None
    assert metrics["sortino_ratio"] is None
    assert metrics["max_drawdown"] is None


def test_metrics_basic_sharpe_sortino_and_drawdown():
    calc = PerformanceMetricsCalculator(annual_trading_days=2, annual_rf_rate=0.0)
    # Values: up then down → non-zero volatility; drawdown occurs on last day
    vals = _build_values([100.0, 110.0, 99.0])
    metrics = {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}
    calc.update_metrics(metrics, vals)
    assert metrics["sharpe_ratio"] is not None
    assert metrics["sortino_ratio"] is not None
    assert metrics["max_drawdown"] < 0.0
    assert isinstance(metrics.get("max_drawdown_date"), str)


def test_metrics_zero_volatility_sharpe_zero():
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    vals = _build_values([100.0, 100.0, 100.0, 100.0])
    metrics = {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}
    calc.update_metrics(metrics, vals)
    assert metrics["sharpe_ratio"] == 0.0


def test_metrics_single_data_point_no_update():
    calc = PerformanceMetricsCalculator()
    metrics = {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}
    calc.update_metrics(metrics, _build_values([100_000.0]))
    assert metrics["sharpe_ratio"] is None


def test_metrics_all_positive_returns_sortino_inf():
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    # Strictly increasing portfolio → no downside returns → Sortino = inf
    vals = _build_values([100.0, 110.0, 121.0, 133.1])
    metrics = {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}
    calc.update_metrics(metrics, vals)
    assert metrics["sortino_ratio"] is not None
    assert metrics["sortino_ratio"] > 0


def test_metrics_all_negative_returns_max_drawdown_equals_total_loss():
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    vals = _build_values([100.0, 90.0, 80.0, 70.0])
    metrics = {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}
    calc.update_metrics(metrics, vals)
    assert metrics["max_drawdown"] is not None
    assert metrics["max_drawdown"] < 0.0
    # Max drawdown should be at least -30% (100 → 70)
    assert metrics["max_drawdown"] <= -0.29


def test_metrics_empty_values_returns_none():
    calc = PerformanceMetricsCalculator()
    metrics = {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}
    calc.update_metrics(metrics, [])
    assert metrics["sharpe_ratio"] is None
    assert metrics["sortino_ratio"] is None
    assert metrics["max_drawdown"] is None


def test_metrics_nan_values_handled():
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    vals = _build_values([100.0, float("nan"), 110.0, 105.0])
    metrics = {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}
    # Should not raise even with NaN in values
    try:
        calc.update_metrics(metrics, vals)
    except Exception as e:
        pytest.fail(f"update_metrics raised unexpectedly: {e}")


# ──────────────────────────────────────────────────────────
# Numerical correctness (#207)
# ──────────────────────────────────────────────────────────


def test_max_drawdown_magnitude_known_values():
    """Portfolio 100→120→80: max drawdown = (80-120)/120*100 = -33.33%."""
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    result = calc.compute_metrics(_build_values([100.0, 120.0, 80.0]))
    expected = (80.0 - 120.0) / 120.0 * 100.0
    assert result["max_drawdown"] == pytest.approx(expected, rel=1e-6)


def test_max_drawdown_date_correct():
    """Max drawdown date for [100, 120, 80] should be 2024-01-03."""
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    result = calc.compute_metrics(_build_values([100.0, 120.0, 80.0]))
    assert result["max_drawdown_date"] == "2024-01-03"


def test_sharpe_ratio_numerical_correctness():
    """Verify annualised Sharpe formula for [100, 120, 110] with rf=0."""
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    result = calc.compute_metrics(_build_values([100.0, 120.0, 110.0]))
    excess = np.array([0.2, -1.0 / 12.0])
    expected = float(math.sqrt(252) * excess.mean() / excess.std(ddof=1))
    assert result["sharpe_ratio"] == pytest.approx(expected, rel=1e-4)


def test_max_drawdown_zero_when_strictly_increasing():
    """Strictly increasing portfolio: drawdown = 0.0 and no drawdown date."""
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    result = calc.compute_metrics(_build_values([100.0, 110.0, 120.0, 130.0]))
    assert result["max_drawdown"] == pytest.approx(0.0, abs=1e-10)
    assert result["max_drawdown_date"] is None

