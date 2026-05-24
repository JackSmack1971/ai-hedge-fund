"""Tests for asynchronous flow-run queue behavior and run event streaming."""

from unittest.mock import patch

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

    from app.backend.main import app

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


def _create_flow(client: TestClient) -> int:
    response = client.post("/flows/", json={"name": "Queued Flow", "nodes": [], "edges": []})
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_create_flow_run_enqueues_background_task(client: TestClient):
    flow_id = _create_flow(client)

    with patch("app.backend.routes.flow_runs.process_flow_run_task.delay") as mock_delay:
        response = client.post(f"/flows/{flow_id}/runs/", json={"request_data": {"mode": "test"}})

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "QUEUED"
    mock_delay.assert_called_once_with(data["id"])


def test_flow_run_events_stream_reports_status(client: TestClient):
    flow_id = _create_flow(client)
    with patch("app.backend.routes.flow_runs.process_flow_run_task.delay"):
        create_response = client.post(f"/flows/{flow_id}/runs/", json={"request_data": {"mode": "test"}})
    assert create_response.status_code == 200, create_response.text
    run_id = create_response.json()["id"]

    update_response = client.put(
        f"/flows/{flow_id}/runs/{run_id}",
        json={"status": "COMPLETE", "results": {"ok": True}},
    )
    assert update_response.status_code == 200, update_response.text

    with client.stream("GET", f"/flows/{flow_id}/runs/{run_id}/events") as response:
        assert response.status_code == 200
        first_chunk = next(response.iter_text())
        assert "event: status" in first_chunk
        assert '"status": "COMPLETE"' in first_chunk

