"""Tests asserting /api-keys responses never expose the stored secret value."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.backend.database import get_db
from app.backend.database.models import Base

SECRET = "sk-super-secret-value-12345"


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


def _assert_no_secret(response):
    assert SECRET not in response.text, "raw secret leaked in response body"
    payload = response.json()
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        assert "key_value" not in item, f"key_value field present in response: {item}"


def test_create_does_not_return_secret(client):
    response = client.post(
        "/api-keys/",
        json={"provider": "OPENAI_API_KEY", "key_value": SECRET, "is_active": True},
    )
    assert response.status_code == 200, response.text
    _assert_no_secret(response)
    assert response.json()["has_key"] is True


def test_get_by_provider_does_not_return_secret(client):
    client.post("/api-keys/", json={"provider": "OPENAI_API_KEY", "key_value": SECRET, "is_active": True})
    response = client.get("/api-keys/OPENAI_API_KEY")
    assert response.status_code == 200, response.text
    _assert_no_secret(response)


def test_update_does_not_return_secret(client):
    client.post("/api-keys/", json={"provider": "OPENAI_API_KEY", "key_value": SECRET, "is_active": True})
    response = client.put("/api-keys/OPENAI_API_KEY", json={"key_value": SECRET, "description": "updated"})
    assert response.status_code == 200, response.text
    _assert_no_secret(response)


def test_bulk_update_does_not_return_secret(client):
    response = client.post(
        "/api-keys/bulk",
        json={
            "api_keys": [
                {"provider": "GROQ_API_KEY", "key_value": SECRET, "is_active": True},
                {"provider": "ANTHROPIC_API_KEY", "key_value": SECRET, "is_active": True},
            ]
        },
    )
    assert response.status_code == 200, response.text
    _assert_no_secret(response)


def test_list_does_not_return_secret(client):
    client.post("/api-keys/", json={"provider": "OPENAI_API_KEY", "key_value": SECRET, "is_active": True})
    response = client.get("/api-keys/")
    assert response.status_code == 200, response.text
    _assert_no_secret(response)


def test_create_returns_generic_500_message_on_unexpected_error(client):
    with patch(
        "app.backend.routes.api_keys.ApiKeyRepository.create_or_update_api_key",
        side_effect=RuntimeError("db password=secret"),
    ):
        response = client.post(
            "/api-keys/",
            json={"provider": "OPENAI_API_KEY", "key_value": SECRET, "is_active": True},
        )

    assert response.status_code == 500, response.text
    assert response.json() == {"detail": "An internal error occurred"}
    assert "password=secret" not in response.text
