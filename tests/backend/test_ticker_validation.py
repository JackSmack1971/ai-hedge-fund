from fastapi.testclient import TestClient


def test_run_rejects_injection_style_ticker(test_app: TestClient, monkeypatch):
    monkeypatch.delenv("BACKEND_API_TOKEN", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")

    response = test_app.post(
        "/hedge-fund/run",
        json={
            "tickers": ["AAPL&evil=1"],
            "graph_nodes": [],
            "graph_edges": [],
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("tickers" in ".".join(str(part) for part in error["loc"]) for error in detail)
