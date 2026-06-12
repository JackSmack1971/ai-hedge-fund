"""Tests for request sanitization in the hedge-fund run route."""

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


def test_run_route_strips_api_keys_before_graph_execution(client: TestClient):
    captured_request = {}

    async def fake_run_graph_async(**kwargs):
        captured_request["request"] = kwargs["request"]
        return {
            "messages": [],
            "data": {"analyst_signals": {}, "current_prices": {}},
        }

    with patch("app.backend.routes.hedge_fund.run_graph_async", side_effect=fake_run_graph_async):
        response = client.post(
            "/hedge-fund/run",
            json={
                "tickers": ["AAPL"],
                "graph_nodes": [],
                "graph_edges": [],
                "model_name": "gpt-4.1",
                "model_provider": "OpenAI",
                "api_keys": {"OPENAI_API_KEY": "secret"},
            },
        )

    assert response.status_code == 200, response.text
    assert captured_request["request"].api_keys is None
