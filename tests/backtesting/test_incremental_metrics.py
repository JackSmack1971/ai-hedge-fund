"""Regression tests for #159 — incremental O(1) metrics via add_value()."""

import math
from datetime import datetime, timedelta

import pytest

from src.backtesting.metrics import PerformanceMetricsCalculator


def _dt(i: int) -> datetime:
    return datetime(2024, 1, 1) + timedelta(days=i)


def _feed(calc: PerformanceMetricsCalculator, values: list[float]):
    """Feed a list of portfolio values incrementally, return final metrics."""
    result = None
    for i, v in enumerate(values):
        result = calc.add_value(v, _dt(i))
    return result


def _batch(values: list[float]) -> dict:
    """Compute metrics via the full batch path."""
    calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
    from datetime import datetime, timedelta

    points = [
        {
            "Date": datetime(2024, 1, 1) + timedelta(days=i),
            "Portfolio Value": v,
            "Long Exposure": 0.0,
            "Short Exposure": 0.0,
            "Gross Exposure": 0.0,
            "Net Exposure": 0.0,
            "Long/Short Ratio": 0.0,
        }
        for i, v in enumerate(values)
    ]
    return calc.compute_metrics(points)


class TestAddValueBasic:
    def test_single_value_returns_none(self):
        calc = PerformanceMetricsCalculator(annual_rf_rate=0.0)
        result = calc.add_value(100_000.0, _dt(0))
        assert result is None

    def test_two_values_returns_none(self):
        calc = PerformanceMetricsCalculator(annual_rf_rate=0.0)
        calc.add_value(100_000.0, _dt(0))
        result = calc.add_value(110_000.0, _dt(1))
        assert result is None

    def test_three_values_returns_metrics(self):
        calc = PerformanceMetricsCalculator(annual_rf_rate=0.0)
        result = _feed(calc, [100.0, 110.0, 99.0])
        assert result is not None
        assert "sharpe_ratio" in result
        assert "sortino_ratio" in result
        assert "max_drawdown" in result

    def test_zero_volatility_sharpe_zero(self):
        calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
        result = _feed(calc, [100.0, 100.0, 100.0, 100.0])
        assert result is not None
        assert result["sharpe_ratio"] == 0.0

    def test_all_positive_returns_sortino_inf(self):
        calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=0.0)
        result = _feed(calc, [100.0, 110.0, 121.0, 133.1])
        assert result is not None
        assert result["sortino_ratio"] == float("inf")

    def test_max_drawdown_correct_direction(self):
        """Drawdown from 110→99 is (99-110)/110 ≈ -10%."""
        calc = PerformanceMetricsCalculator(annual_rf_rate=0.0)
        result = _feed(calc, [100.0, 110.0, 99.0])
        assert result["max_drawdown"] < 0.0

    def test_max_drawdown_date_set(self):
        calc = PerformanceMetricsCalculator(annual_rf_rate=0.0)
        result = _feed(calc, [100.0, 110.0, 99.0])
        assert result["max_drawdown_date"] is not None
        assert isinstance(result["max_drawdown_date"], str)

    def test_no_drawdown_date_when_always_rising(self):
        calc = PerformanceMetricsCalculator(annual_rf_rate=0.0)
        result = _feed(calc, [100.0, 110.0, 121.0])
        assert result["max_drawdown_date"] is None

    def test_reset_between_instances(self):
        """Two separate calculators produce independent results."""
        c1 = PerformanceMetricsCalculator(annual_rf_rate=0.0)
        c2 = PerformanceMetricsCalculator(annual_rf_rate=0.0)
        _feed(c1, [100.0, 110.0, 99.0])
        r2 = _feed(c2, [100.0, 100.0, 100.0, 100.0])
        assert r2["sharpe_ratio"] == 0.0


class TestIncrementalMatchesBatch:
    """Verify add_value() produces numerically identical results to compute_metrics()."""

    def _close(self, a, b, rel=1e-9):
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if not math.isfinite(a) and not math.isfinite(b):
            return True
        return abs(a - b) <= rel * max(abs(a), abs(b), 1.0)

    def _check_parity(self, values: list[float], rf: float = 0.0):
        calc = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=rf)
        incremental = _feed(calc, values)
        batch = _batch(values)
        # batch uses rf=0.0; if rf≠0 use separate calc for batch
        if rf != 0.0:
            calc_b = PerformanceMetricsCalculator(annual_trading_days=252, annual_rf_rate=rf)
            from datetime import datetime, timedelta

            points = [
                {
                    "Date": datetime(2024, 1, 1) + timedelta(days=i),
                    "Portfolio Value": v,
                    "Long Exposure": 0.0,
                    "Short Exposure": 0.0,
                    "Gross Exposure": 0.0,
                    "Net Exposure": 0.0,
                    "Long/Short Ratio": 0.0,
                }
                for i, v in enumerate(values)
            ]
            batch = calc_b.compute_metrics(points)
        assert self._close(
            incremental["sharpe_ratio"], batch["sharpe_ratio"]
        ), f"Sharpe mismatch: incremental={incremental['sharpe_ratio']}, batch={batch['sharpe_ratio']}"
        assert self._close(
            incremental["max_drawdown"], batch["max_drawdown"]
        ), f"MaxDD mismatch: incremental={incremental['max_drawdown']}, batch={batch['max_drawdown']}"

    def test_parity_up_down(self):
        self._check_parity([100.0, 110.0, 99.0, 105.0, 95.0])

    def test_parity_monotone_increase(self):
        self._check_parity([100.0 * (1.01**i) for i in range(20)])

    def test_parity_monotone_decrease(self):
        self._check_parity([100.0 * (0.99**i) for i in range(20)])

    def test_parity_flat(self):
        self._check_parity([100.0] * 10)

    def test_parity_volatile(self):
        import random

        random.seed(42)
        vals = [100_000.0]
        for _ in range(50):
            vals.append(vals[-1] * (1 + random.gauss(0, 0.02)))
        self._check_parity(vals)

    def test_parity_with_nonzero_rf(self):
        self._check_parity([100.0, 110.0, 99.0, 105.0, 95.0], rf=0.04)
