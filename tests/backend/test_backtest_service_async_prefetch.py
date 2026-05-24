from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.backend.services.backtest_service import BacktestService


class _FakeLoop:
    def __init__(self):
        self.called = False
        self.executor = None
        self.func = None

    async def run_in_executor(self, executor, func):
        self.called = True
        self.executor = executor
        self.func = func
        func()
        return None


@pytest.mark.asyncio
async def test_run_backtest_async_prefetches_in_executor(monkeypatch):
    fake_loop = _FakeLoop()
    monkeypatch.setattr("app.backend.services.backtest_service.asyncio.get_running_loop", lambda: fake_loop)
    monkeypatch.setattr("app.backend.services.backtest_service.pd.date_range", lambda *args, **kwargs: [])

    service = BacktestService(
        graph=MagicMock(),
        portfolio={"cash": 1000.0, "margin_requirement": 0.0, "positions": {}, "realized_gains": {}, "margin_used": 0.0},
        tickers=[],
        start_date="2024-01-01",
        end_date="2024-01-02",
        initial_capital=1000.0,
        request=SimpleNamespace(api_keys={}),
    )
    service.prefetch_data = MagicMock()

    await service.run_backtest_async()

    assert fake_loop.called is True
    assert fake_loop.executor is None
    service.prefetch_data.assert_called_once()

