"""Tests for src/backtesting/benchmarks.py."""

from unittest.mock import patch

import pandas as pd
import pytest

from src.backtesting.benchmarks import BenchmarkCalculator


def _make_price_df(closes: list[float]) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    df = pd.DataFrame({"close": closes}, index=dates)
    return df


class TestBenchmarkCalculator:
    def setup_method(self):
        self.calc = BenchmarkCalculator()

    @patch("src.backtesting.benchmarks.get_price_data")
    def test_positive_return(self, mock_get_price):
        mock_get_price.return_value = _make_price_df([100.0, 110.0, 120.0])
        result = self.calc.get_return_pct("AAPL", "2024-01-01", "2024-01-03")
        assert result is not None
        assert abs(result - 20.0) < 1e-6

    @patch("src.backtesting.benchmarks.get_price_data")
    def test_negative_return(self, mock_get_price):
        mock_get_price.return_value = _make_price_df([100.0, 90.0, 80.0])
        result = self.calc.get_return_pct("AAPL", "2024-01-01", "2024-01-03")
        assert result is not None
        assert abs(result - (-20.0)) < 1e-6

    @patch("src.backtesting.benchmarks.get_price_data")
    def test_zero_return(self, mock_get_price):
        mock_get_price.return_value = _make_price_df([100.0, 100.0, 100.0])
        result = self.calc.get_return_pct("AAPL", "2024-01-01", "2024-01-03")
        assert result == 0.0

    @patch("src.backtesting.benchmarks.get_price_data")
    def test_empty_dataframe_returns_none(self, mock_get_price):
        mock_get_price.return_value = pd.DataFrame()
        result = self.calc.get_return_pct("AAPL", "2024-01-01", "2024-01-03")
        assert result is None

    @patch("src.backtesting.benchmarks.get_price_data")
    def test_single_price_point_returns_zero(self, mock_get_price):
        mock_get_price.return_value = _make_price_df([150.0])
        result = self.calc.get_return_pct("AAPL", "2024-01-01", "2024-01-01")
        assert result == 0.0

    @patch("src.backtesting.benchmarks.get_price_data")
    def test_exception_returns_none(self, mock_get_price):
        mock_get_price.side_effect = Exception("API error")
        result = self.calc.get_return_pct("AAPL", "2024-01-01", "2024-01-03")
        assert result is None

    @patch("src.backtesting.benchmarks.get_price_data")
    def test_nan_first_close_returns_none(self, mock_get_price):
        import numpy as np

        df = _make_price_df([100.0, 110.0])
        df.iloc[0, df.columns.get_loc("close")] = float("nan")
        mock_get_price.return_value = df
        result = self.calc.get_return_pct("AAPL", "2024-01-01", "2024-01-02")
        assert result is None

    @patch("src.backtesting.benchmarks.get_price_data")
    def test_large_gain(self, mock_get_price):
        mock_get_price.return_value = _make_price_df([10.0, 20.0])
        result = self.calc.get_return_pct("TSLA", "2024-01-01", "2024-01-02")
        assert result is not None
        assert abs(result - 100.0) < 1e-6
