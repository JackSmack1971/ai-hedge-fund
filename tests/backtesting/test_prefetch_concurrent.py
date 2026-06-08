"""Regression tests for #163 — concurrent prefetch in _prefetch_data()."""

from unittest.mock import call, MagicMock, patch

import pytest


class TestPrefetchConcurrent:
    def _make_engine(self, tickers=None):
        """Build a BacktestEngine with mocked agent and minimal config."""
        from src.backtesting.engine import BacktestEngine

        return BacktestEngine(
            agent=MagicMock(),
            tickers=tickers or ["AAPL", "MSFT"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100_000.0,
            model_name="gpt-4o",
            model_provider="OpenAI",
            selected_analysts=None,
            initial_margin_requirement=0.0,
        )

    @patch("src.backtesting.engine.get_company_news", return_value=[])
    @patch("src.backtesting.engine.get_insider_trades", return_value=[])
    @patch("src.backtesting.engine.get_financial_metrics", return_value=[])
    @patch("src.backtesting.engine.get_prices", return_value=[])
    def test_all_tickers_fetched(self, mock_prices, mock_metrics, mock_trades, mock_news):
        """Every ticker should have prices, metrics, trades, and news fetched."""
        engine = self._make_engine(["AAPL", "MSFT"])
        engine._prefetch_data()

        tickers_fetched = {c.args[0] for c in mock_prices.call_args_list}
        assert "AAPL" in tickers_fetched
        assert "MSFT" in tickers_fetched
        assert "SPY" in tickers_fetched

    @patch("src.backtesting.engine.get_company_news", return_value=[])
    @patch("src.backtesting.engine.get_insider_trades", return_value=[])
    @patch("src.backtesting.engine.get_financial_metrics", return_value=[])
    @patch("src.backtesting.engine.get_prices", return_value=[])
    def test_spy_benchmark_prefetched(self, mock_prices, mock_metrics, mock_trades, mock_news):
        """SPY should always be prefetched for benchmark comparison."""
        engine = self._make_engine(["AAPL"])
        engine._prefetch_data()
        spy_calls = [c for c in mock_prices.call_args_list if c.args[0] == "SPY"]
        assert len(spy_calls) == 1

    @patch("src.backtesting.engine.get_company_news", return_value=[])
    @patch("src.backtesting.engine.get_insider_trades", return_value=[])
    @patch("src.backtesting.engine.get_financial_metrics", return_value=[])
    @patch("src.backtesting.engine.get_prices", return_value=[])
    def test_total_task_count(self, mock_prices, mock_metrics, mock_trades, mock_news):
        """2 tickers × 4 calls + 1 SPY = 9 total tasks."""
        engine = self._make_engine(["AAPL", "MSFT"])
        engine._prefetch_data()
        assert mock_prices.call_count == 3  # AAPL + MSFT + SPY
        assert mock_metrics.call_count == 2
        assert mock_trades.call_count == 2
        assert mock_news.call_count == 2

    @patch("src.backtesting.engine.get_company_news", side_effect=RuntimeError("API down"))
    @patch("src.backtesting.engine.get_insider_trades", return_value=[])
    @patch("src.backtesting.engine.get_financial_metrics", return_value=[])
    @patch("src.backtesting.engine.get_prices", return_value=[])
    def test_exception_surfaces(self, mock_prices, mock_metrics, mock_trades, mock_news):
        """Exceptions from individual fetch tasks should propagate, not be swallowed."""
        engine = self._make_engine(["AAPL"])
        with pytest.raises(RuntimeError, match="API down"):
            engine._prefetch_data()

    @patch("src.backtesting.engine.get_company_news", return_value=[])
    @patch("src.backtesting.engine.get_insider_trades", return_value=[])
    @patch("src.backtesting.engine.get_financial_metrics", return_value=[])
    @patch("src.backtesting.engine.get_prices", return_value=[])
    def test_single_ticker_still_works(self, mock_prices, mock_metrics, mock_trades, mock_news):
        """Single-ticker prefetch should work without errors."""
        engine = self._make_engine(["AAPL"])
        engine._prefetch_data()
        assert mock_prices.call_count == 2  # AAPL + SPY
