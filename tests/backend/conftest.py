"""Shared fixtures for backend tests."""

import os
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "app" / "backend"
TEST_DB_PATH = Path(tempfile.gettempdir()) / f"ai-hedge-fund-backend-tests-{os.getpid()}.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["AUTO_CREATE_TABLES"] = "false"

from app.backend.database.connection import engine


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    # Prevent Alembic from reconfiguring the Python logging system during tests,
    # which would replace pytest's caplog handler and break log-capture assertions.
    config.config_file_name = None
    return config


def _reset_backend_database() -> None:
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    command.upgrade(_alembic_config(), "head")


@pytest.fixture(autouse=True)
def _database_encryption_key(monkeypatch):
    """Stored-API-key writes fail closed without DATABASE_ENCRYPTION_KEY; provide one for tests."""
    monkeypatch.setenv("DATABASE_ENCRYPTION_KEY", "backend-test-encryption-key")


@pytest.fixture(scope="function")
def db_session():
    """Alembic-backed SQLite session for each test — hermetic, no create_all bootstrap."""
    _reset_backend_database()
    with Session(engine) as session:
        yield session
    session.close()
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="module")
def test_app():
    """FastAPI TestClient backed by Alembic-managed schema."""
    _reset_backend_database()

    from app.backend.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
