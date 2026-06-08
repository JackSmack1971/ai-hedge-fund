"""Shared fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.backend.database.connection import DATABASE_URL
from app.backend.database.models import Base


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
    from unittest.mock import AsyncMock, patch

    with patch("app.backend.database.connection.engine"):
        with patch("app.backend.database.models.Base.metadata.create_all"):
            from app.backend.main import app

            with TestClient(app, raise_server_exceptions=False) as client:
                yield client
