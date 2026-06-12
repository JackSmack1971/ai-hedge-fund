"""Tests for FastAPI health/root routes."""

import pytest
from fastapi.testclient import TestClient

from app.backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_message(self, client):
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "plaintext_api_keys_remaining" in data
        assert isinstance(data["plaintext_api_keys_remaining"], int)

    def test_root_sets_security_headers(self, client):
        response = client.get("/")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["cache-control"] == "no-store"
