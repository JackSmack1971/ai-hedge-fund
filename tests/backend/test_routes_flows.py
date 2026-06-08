"""Tests for /flows routes using in-memory SQLite and TestClient."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
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


class TestFlowsCreate:
    def test_create_flow_valid(self, client):
        payload = {"name": "Test Flow", "nodes": [{"id": "n1"}], "edges": []}
        response = client.post("/flows/", json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == "Test Flow"
        assert "id" in data

    def test_create_flow_missing_name_returns_422(self, client):
        response = client.post("/flows/", json={"nodes": [], "edges": []})
        assert response.status_code == 422

    def test_create_flow_empty_name_returns_422(self, client):
        response = client.post("/flows/", json={"name": "", "nodes": [], "edges": []})
        assert response.status_code == 422


class TestFlowsGet:
    def test_get_all_flows_returns_list(self, client):
        response = client.get("/flows/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_flow_by_id_existing(self, client):
        create_resp = client.post("/flows/", json={"name": "Flow X", "nodes": [], "edges": []})
        assert create_resp.status_code == 200, create_resp.text
        flow_id = create_resp.json()["id"]
        response = client.get(f"/flows/{flow_id}")
        assert response.status_code == 200
        assert response.json()["id"] == flow_id

    def test_get_flow_by_id_missing_returns_404(self, client):
        response = client.get("/flows/99999")
        assert response.status_code == 404


class TestFlowsDelete:
    def test_delete_existing_flow(self, client):
        create_resp = client.post("/flows/", json={"name": "Flow To Delete", "nodes": [], "edges": []})
        assert create_resp.status_code == 200, create_resp.text
        flow_id = create_resp.json()["id"]
        del_resp = client.delete(f"/flows/{flow_id}")
        assert del_resp.status_code == 200
        get_resp = client.get(f"/flows/{flow_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_flow(self, client):
        response = client.delete("/flows/99998")
        assert response.status_code == 404
