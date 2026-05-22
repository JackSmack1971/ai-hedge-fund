from __future__ import annotations

from typing import Sequence

from .types import PerformanceMetrics, PortfolioValuePoint


class PerformanceMetricsCalculator:
    """Concrete metrics calculator like sharpe ratio, sortino ratio, max drawdown, etc."""

    def __init__(self, *, annual_trading_days: int = 252, annual_rf_rate: float = 0.0434) -> None:
        self.annual_trading_days = annual_trading_days
        self.annual_rf_rate = annual_rf_rate
        self._reset_incremental()

    # ------------------------------------------------------------------
    # Incremental O(1) path — used by BacktestEngine
    # ------------------------------------------------------------------

    def _reset_incremental(self) -> None:
        """Reset all incremental state."""
        # Welford online mean+variance for excess returns
        self._n: int = 0
        self._mean_excess: float = 0.0
        self._M2_excess: float = 0.0
        # Welford for downside excess returns only
        self._n_down: int = 0
        self._mean_down: float = 0.0
        self._M2_down: float = 0.0
        # Running max for drawdown
        self._running_max: float = 0.0
        self._min_drawdown: float = 0.0
        self._min_drawdown_date = None
        # Previous value for return calculation
        self._prev_value: float | None = None

    def add_value(self, value: float, date) -> PerformanceMetrics | None:
        """Feed one portfolio value; returns updated metrics or None if insufficient data.

        Uses Welford online algorithm — O(1) per call, no DataFrame rebuild.
        """
        daily_rf = self.annual_rf_rate / self.annual_trading_days

        if self._prev_value is not None and self._prev_value > 0:
            ret = (value - self._prev_value) / self._prev_value
            excess = ret - daily_rf

            # Welford update for all excess returns
            self._n += 1
            delta = excess - self._mean_excess
            self._mean_excess += delta / self._n
            self._M2_excess += delta * (excess - self._mean_excess)

            # Welford update for downside excess returns
            if excess < 0:
                self._n_down += 1
                delta_d = excess - self._mean_down
                self._mean_down += delta_d / self._n_down
                self._M2_down += delta_d * (excess - self._mean_down)

        # Running max and max-drawdown update
        self._running_max = max(self._running_max, value)
        if self._running_max > 0:
            dd = (value - self._running_max) / self._running_max
            if dd < self._min_drawdown:
                self._min_drawdown = dd
                self._min_drawdown_date = date

        self._prev_value = value

        return self._incremental_metrics() if self._n >= 2 else None

    def _incremental_metrics(self) -> PerformanceMetrics:
        # Sharpe (sample std, ddof=1)
        std_excess = (self._M2_excess / (self._n - 1)) ** 0.5
        if std_excess > 1e-12:
            sharpe = float(self.annual_trading_days ** 0.5 * (self._mean_excess / std_excess))
        else:
            sharpe = 0.0

        # Sortino: downside std (sample, ddof=1); treat n_down≤1 same as NaN (→ inf/0)
        if self._n_down >= 2:
            downside_std = (self._M2_down / (self._n_down - 1)) ** 0.5
            if downside_std > 1e-12:
                sortino = float(self.annual_trading_days ** 0.5 * (self._mean_excess / downside_std))
            else:
                sortino = float("inf") if self._mean_excess > 0 else 0.0
        else:
            sortino = float("inf") if self._mean_excess > 0 else 0.0

        max_drawdown = float(self._min_drawdown * 100.0)
        if self._min_drawdown_date is not None and hasattr(self._min_drawdown_date, "strftime"):
            max_drawdown_date: str | None = self._min_drawdown_date.strftime("%Y-%m-%d")
        else:
            max_drawdown_date = None

        return {
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": max_drawdown,
            "max_drawdown_date": max_drawdown_date,
        }

    # ------------------------------------------------------------------
    # Batch path — kept for backward compatibility with existing tests
    # ------------------------------------------------------------------

    def update_metrics(self, metrics: PerformanceMetrics, values: Sequence[PortfolioValuePoint]) -> None:
        """Deprecated: mutate provided dict. Kept for backward compatibility."""
        computed = self.compute_metrics(values)
        if not computed:
            return
        metrics.update(computed)  # type: ignore[arg-type]

    def compute_metrics(self, values: Sequence[PortfolioValuePoint]) -> PerformanceMetrics:
        import pandas as pd
        import numpy as np

        if not values:
            return {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}

        df = pd.DataFrame(values)
        if df.empty or "Portfolio Value" not in df:
            return {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}

        df = df.set_index("Date")
        df["Daily Return"] = df["Portfolio Value"].pct_change()
        clean_returns = df["Daily Return"].dropna()
        if len(clean_returns) < 2:
            return {"sharpe_ratio": None, "sortino_ratio": None, "max_drawdown": None}

        daily_rf = self.annual_rf_rate / self.annual_trading_days
        excess = clean_returns - daily_rf
        mean_excess = excess.mean()
        std_excess = excess.std()

        if std_excess > 1e-12:
            sharpe = float(np.sqrt(self.annual_trading_days) * (mean_excess / std_excess))
        else:
            sharpe = 0.0

        negative_excess = excess[excess < 0]
        if len(negative_excess) > 0:
            downside_std = negative_excess.std()
            if downside_std > 1e-12:
                sortino = float(np.sqrt(self.annual_trading_days) * (mean_excess / downside_std))
            else:
                sortino = float("inf") if mean_excess > 0 else 0.0
        else:
            sortino = float("inf") if mean_excess > 0 else 0.0

        rolling_max = df["Portfolio Value"].cummax()
        drawdown = (df["Portfolio Value"] - rolling_max) / rolling_max
        if len(drawdown) > 0:
            min_dd = float(drawdown.min())
            max_drawdown = float(min_dd * 100.0)
            if min_dd < 0:
                max_drawdown_date = drawdown.idxmin().strftime("%Y-%m-%d")
            else:
                max_drawdown_date = None
        else:
            max_drawdown = 0.0
            max_drawdown_date = None

        return {
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": max_drawdown,
            "max_drawdown_date": max_drawdown_date,
        }
