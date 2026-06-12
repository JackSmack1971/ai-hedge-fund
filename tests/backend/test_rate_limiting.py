"""Tests for backend rate limiting."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.backend.database import get_db
from app.backend.database.models import Base


@pytest.fixture(scope="module")
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    with patch(
        "app.backend.services.ollama_service.ollama_service.check_ollama_status",
        new=AsyncMock(return_value={"installed": True, "running": True, "available_models": [], "server_url": ""}),
    ):
        from app.backend.main import app

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
        app.dependency_overrides.pop(get_db, None)

    Base.metadata.drop_all(engine)


def test_hedge_fund_run_is_rate_limited(client: TestClient, monkeypatch):
    monkeypatch.setenv("HEDGE_FUND_RUN_RATE_LIMIT_PER_MINUTE", "1")

    async def fake_run_graph_async(**kwargs):
        return {"messages": [], "data": {"analyst_signals": {}, "current_prices": {}}}

    payload = {
        "tickers": ["AAPL"],
        "graph_nodes": [],
        "graph_edges": [],
        "initial_cash": 100000.0,
        "api_keys": {"OPENAI_API_KEY": "secret"},
    }

    with patch("app.backend.routes.hedge_fund.run_graph_async", side_effect=fake_run_graph_async):
        first = client.post("/hedge-fund/run", json=payload)
        second = client.post("/hedge-fund/run", json=payload)

    assert first.status_code == 200, first.text
    assert second.status_code == 429
    assert second.json()["detail"] == "Rate limit exceeded"
