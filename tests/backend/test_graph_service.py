from unittest.mock import patch

import pytest

from app.backend.services.graph import GRAPH_EXECUTOR, run_graph_async


@pytest.mark.asyncio
async def test_run_graph_async_uses_dedicated_executor():
    class DummyLoop:
        def __init__(self):
            self.executor = None
            self.callback = None

        async def run_in_executor(self, executor, callback):
            self.executor = executor
            self.callback = callback
            return callback()

    dummy_loop = DummyLoop()

    with patch("app.backend.services.graph.asyncio.get_running_loop", return_value=dummy_loop):
        with patch("app.backend.services.graph.run_graph", return_value={"ok": True}) as mock_run_graph:
            result = await run_graph_async("graph", {}, [], "2024-01-01", "2024-01-02", "model", "provider")

    assert result == {"ok": True}
    assert dummy_loop.executor is GRAPH_EXECUTOR
    mock_run_graph.assert_called_once()
