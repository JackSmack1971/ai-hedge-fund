"""Regression tests for #167 — DB session released before streaming begins."""
import pytest
import asyncio
from unittest.mock import MagicMock, patch


_GRAPH_NODES = [{"id": "n1", "type": "analyst"}]
_GRAPH_EDGES: list = []


class TestDbSessionReleasedBeforeStreaming:
    """Both /run and /backtest must call db.close() before returning StreamingResponse."""

    def _mock_db(self):
        db = MagicMock()
        db.close = MagicMock()
        return db

    def test_run_endpoint_closes_db_session(self):
        """run() endpoint closes the db session before streaming."""
        from app.backend.routes.hedge_fund import run
        from app.backend.models.schemas import HedgeFundRequest

        db = self._mock_db()

        with patch("app.backend.routes.hedge_fund.ApiKeyService") as mock_svc_cls, \
             patch("app.backend.routes.hedge_fund.create_portfolio", return_value=MagicMock()), \
             patch("app.backend.routes.hedge_fund.create_graph", return_value=MagicMock()), \
             patch("app.backend.routes.hedge_fund.progress"):
            mock_svc = MagicMock()
            mock_svc.get_api_keys_dict.return_value = {}
            mock_svc_cls.return_value = mock_svc

            request_data = HedgeFundRequest(
                tickers=["AAPL"],
                graph_nodes=_GRAPH_NODES,
                graph_edges=_GRAPH_EDGES,
                start_date="2024-01-01",
                end_date="2024-03-31",
                model_name="gpt-4o",
                model_provider="OpenAI",
            )

            asyncio.get_event_loop().run_until_complete(run(request_data, MagicMock(), db))

        db.close.assert_called_once()

    def test_backtest_endpoint_closes_db_session(self):
        """backtest() endpoint closes the db session before streaming."""
        from app.backend.routes.hedge_fund import backtest
        from app.backend.models.schemas import BacktestRequest

        db = self._mock_db()

        with patch("app.backend.routes.hedge_fund.ApiKeyService") as mock_svc_cls, \
             patch("app.backend.routes.hedge_fund.create_portfolio", return_value=MagicMock()), \
             patch("app.backend.routes.hedge_fund.create_graph", return_value=MagicMock()), \
             patch("app.backend.routes.hedge_fund.BacktestService", return_value=MagicMock()), \
             patch("app.backend.routes.hedge_fund.progress"):
            mock_svc = MagicMock()
            mock_svc.get_api_keys_dict.return_value = {}
            mock_svc_cls.return_value = mock_svc

            request_data = BacktestRequest(
                tickers=["AAPL"],
                graph_nodes=_GRAPH_NODES,
                graph_edges=_GRAPH_EDGES,
                start_date="2024-01-01",
                end_date="2024-03-31",
                model_name="gpt-4o",
                model_provider="OpenAI",
                initial_capital=100_000.0,
            )

            asyncio.get_event_loop().run_until_complete(backtest(request_data, MagicMock(), db))

        db.close.assert_called_once()

    def test_run_closes_db_even_when_api_keys_already_set(self):
        """db.close() is called even when api_keys are pre-populated (skips DB query)."""
        from app.backend.routes.hedge_fund import run
        from app.backend.models.schemas import HedgeFundRequest

        db = self._mock_db()

        with patch("app.backend.routes.hedge_fund.create_portfolio", return_value=MagicMock()), \
             patch("app.backend.routes.hedge_fund.create_graph", return_value=MagicMock()), \
             patch("app.backend.routes.hedge_fund.progress"):

            request_data = HedgeFundRequest(
                tickers=["AAPL"],
                graph_nodes=_GRAPH_NODES,
                graph_edges=_GRAPH_EDGES,
                start_date="2024-01-01",
                end_date="2024-03-31",
                model_name="gpt-4o",
                model_provider="OpenAI",
                api_keys={"OPENAI_API_KEY": "sk-test"},
            )

            asyncio.get_event_loop().run_until_complete(run(request_data, MagicMock(), db))

        db.close.assert_called_once()
