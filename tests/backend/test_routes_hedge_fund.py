"""Tests for hedge-fund route request validation."""


class TestHedgeFundRouteValidation:
    def test_rejects_unknown_model_name(self, test_app):
        response = test_app.post(
            "/hedge-fund/run",
            json={
                "tickers": ["AAPL"],
                "graph_nodes": [{"id": "n1"}],
                "graph_edges": [],
                "model_name": "gpt-evil-injected",
            },
        )

        assert response.status_code == 422
        assert "model_name" in response.text
