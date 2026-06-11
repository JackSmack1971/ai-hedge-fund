"""Regression tests for graph construction and graph execution guards."""

from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph import END

from app.backend.models.schemas import GraphEdge, GraphNode
from app.backend.services.graph import GRAPH_EXECUTOR, create_graph, run_graph, run_graph_async


def test_create_graph_rejects_self_loop():
    """Self-loop edges should be rejected before the graph is built."""
    nodes = [GraphNode(id="warren_buffett_abc123")]
    edges = [GraphEdge(id="e1", source="warren_buffett_abc123", target="warren_buffett_abc123")]

    with pytest.raises(ValueError, match="Self-loop edges are not allowed"):
        create_graph(nodes, edges)


def test_create_graph_rejects_cycle():
    """A -> B -> A should be rejected before the graph is built."""
    nodes = [GraphNode(id="warren_buffett_abc123"), GraphNode(id="ben_graham_def456")]
    edges = [
        GraphEdge(id="e1", source="warren_buffett_abc123", target="ben_graham_def456"),
        GraphEdge(id="e2", source="ben_graham_def456", target="warren_buffett_abc123"),
    ]

    with pytest.raises(ValueError, match="Cyclic graph configurations are not allowed"):
        create_graph(nodes, edges)


def test_run_graph_sets_recursion_limit():
    """run_graph() should pass a bounded recursion limit into graph.invoke()."""
    graph = MagicMock()
    graph.invoke.return_value = {"messages": [], "data": {}}

    result = run_graph(
        graph=graph,
        portfolio={"cash": 1000.0, "margin_requirement": 0.5, "margin_used": 0.0, "equity": 1000.0, "positions": {}},
        tickers=["AAPL"],
        start_date="2024-01-01",
        end_date="2024-01-31",
        model_name="gpt-4.1",
        model_provider="OPENAI",
    )

    assert result == {"messages": [], "data": {}}
    graph.invoke.assert_called_once()
    _, kwargs = graph.invoke.call_args
    assert kwargs["config"] == {"recursion_limit": 50}


class TestCreateGraphTerminalEdges:
    def test_graph_without_portfolio_manager_gets_end_edge(self):
        graph = create_graph(
            graph_nodes=[GraphNode(id="warren_buffett_abc123")],
            graph_edges=[],
        )

        compiled = graph.compile()
        graph_view = compiled.get_graph()
        edge_targets = {edge.target for edge in graph_view.edges if edge.source == "warren_buffett_abc123"}

        assert END in edge_targets


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
