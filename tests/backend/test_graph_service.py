"""Regression tests for graph construction and graph execution guards."""

from unittest.mock import MagicMock

import pytest

from app.backend.models.schemas import GraphEdge, GraphNode
from app.backend.services.graph import create_graph, run_graph


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
