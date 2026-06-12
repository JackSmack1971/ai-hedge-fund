"""Shared fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.backend.database.models import Base


@pytest.fixture(autouse=True)
def _database_encryption_key(monkeypatch):
    """Stored-API-key writes fail closed without DATABASE_ENCRYPTION_KEY; provide one for tests.
    Also sets DISABLE_AUTH=true so PR-87 fail-closed auth doesn't block non-auth tests.
    Individual auth tests override this with monkeypatch.delenv('DISABLE_AUTH').
    """
    monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", "backend-test-encryption-key")
    monkeypatch.setenv("DISABLE_AUTH", "true")


@pytest.fixture(scope="function")
def db_session():
    """In-memory SQLite session for each test — hermetic, no real DB required."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def test_app():
    """FastAPI TestClient with startup events skipped."""
    from unittest.mock import patch

    with patch("app.backend.database.connection.engine"):
        with patch("app.backend.database.models.Base.metadata.create_all"):
            from app.backend.main import app

            with TestClient(app, raise_server_exceptions=False) as client:
                yield client
