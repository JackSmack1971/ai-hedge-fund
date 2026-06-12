"""Tests for app/backend/services/graph.py graph assembly."""

from langgraph.graph import END

from app.backend.models.schemas import GraphNode
from app.backend.services.graph import create_graph


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
