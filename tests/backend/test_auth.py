"""Tests for BACKEND_API_TOKEN bearer-token enforcement on backend routes."""

import pytest
from fastapi.testclient import TestClient

TOKEN = "test-backend-token"


@pytest.fixture(scope="module")
def client(test_app):
    """Delegate to the conftest Alembic-backed test_app fixture."""
    return test_app


class TestTokenEnforced:
    """With BACKEND_API_TOKEN set, protected routes require a matching bearer token."""

    def test_missing_token_rejected(self, client, monkeypatch):
        monkeypatch.setenv("BACKEND_API_TOKEN", TOKEN)
        response = client.get("/flows/")
        assert response.status_code in (401, 403)

    def test_invalid_token_rejected(self, client, monkeypatch):
        monkeypatch.setenv("BACKEND_API_TOKEN", TOKEN)
        response = client.get("/flows/", headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 401

    def test_valid_token_accepted(self, client, monkeypatch):
        monkeypatch.setenv("BACKEND_API_TOKEN", TOKEN)
        response = client.get("/flows/", headers={"Authorization": f"Bearer {TOKEN}"})
        assert response.status_code == 200

    def test_api_keys_route_protected(self, client, monkeypatch):
        monkeypatch.setenv("BACKEND_API_TOKEN", TOKEN)
        assert client.get("/api-keys/").status_code in (401, 403)
        assert client.get("/api-keys/", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200

    def test_storage_route_protected(self, client, monkeypatch):
        monkeypatch.setenv("BACKEND_API_TOKEN", TOKEN)
        response = client.post("/storage/save-json", json={"filename": "x.json", "data": {}})
        assert response.status_code in (401, 403)

    def test_health_route_stays_open(self, client, monkeypatch):
        monkeypatch.setenv("BACKEND_API_TOKEN", TOKEN)
        response = client.get("/")
        assert response.status_code == 200


class TestTokenUnset:
    def test_development_allows_requests(self, client, monkeypatch):
        monkeypatch.delenv("BACKEND_API_TOKEN", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "development")
        response = client.get("/flows/")
        assert response.status_code == 200

    def test_production_fails_closed(self, client, monkeypatch):
        monkeypatch.delenv("BACKEND_API_TOKEN", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "production")
        response = client.get("/flows/")
        assert response.status_code == 503
