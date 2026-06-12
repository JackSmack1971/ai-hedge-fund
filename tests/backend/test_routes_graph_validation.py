"""Regression tests for invalid graph rejection at the HTTP boundary."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.backend.models.schemas import BacktestRequest, HedgeFundRequest
from app.backend.routes.hedge_fund import backtest, run


def _mock_db():
    db = MagicMock()
    db.close = MagicMock()
    return db


class TestGraphValidationRoutes:
    def test_run_rejects_self_loop_graph(self):
        """/hedge-fund/run returns HTTP 400 for a self-loop graph."""
        request_data = HedgeFundRequest(
            tickers=["AAPL"],
            graph_nodes=[{"id": "warren_buffett_abc123"}],
            graph_edges=[
                {
                    "id": "e1",
                    "source": "warren_buffett_abc123",
                    "target": "warren_buffett_abc123",
                }
            ],
            start_date="2024-01-01",
            end_date="2024-03-31",
            model_name="gpt-4o",
            model_provider="OpenAI",
            api_keys={"OPENAI_API_KEY": "sk-test"},
        )

        with patch("app.backend.routes.hedge_fund.create_portfolio", return_value=MagicMock()):
            with pytest.raises(HTTPException) as excinfo:
                asyncio.run(run(request_data, MagicMock(), _mock_db()))

        assert excinfo.value.status_code == 400
        assert "Self-loop edges are not allowed" in excinfo.value.detail

    def test_backtest_rejects_cyclic_graph(self):
        """/hedge-fund/backtest returns HTTP 400 for a cyclic graph."""
        request_data = BacktestRequest(
            tickers=["AAPL"],
            graph_nodes=[
                {"id": "warren_buffett_abc123"},
                {"id": "ben_graham_def456"},
            ],
            graph_edges=[
                {"id": "e1", "source": "warren_buffett_abc123", "target": "ben_graham_def456"},
                {"id": "e2", "source": "ben_graham_def456", "target": "warren_buffett_abc123"},
            ],
            start_date="2024-01-01",
            end_date="2024-03-31",
            model_name="gpt-4o",
            model_provider="OpenAI",
            initial_capital=100_000.0,
            api_keys={"OPENAI_API_KEY": "sk-test"},
        )

        with patch("app.backend.routes.hedge_fund.create_portfolio", return_value=MagicMock()):
            with pytest.raises(HTTPException) as excinfo:
                asyncio.run(backtest(request_data, MagicMock(), _mock_db()))

        assert excinfo.value.status_code == 400
        assert "Cyclic graph configurations are not allowed" in excinfo.value.detail
