"""Regression tests for centralized environment access."""

from pathlib import Path


_TARGET_FILES = [
    "src/tools/api.py",
    "src/llm/models.py",
    "src/utils/ollama.py",
    "src/main.py",
    "app/backend/auth.py",
    "app/backend/encryption.py",
    "app/backend/database/connection.py",
    "app/backend/tasks/celery_app.py",
    "app/backend/alembic/env.py",
    "app/backend/main.py",
]


def test_business_modules_use_shared_settings_modules():
    """The business modules should not read env vars directly anymore."""
    for rel_path in _TARGET_FILES:
        source = Path(rel_path).read_text(encoding="utf-8")
        assert "os.environ.get(" not in source
        assert "os.getenv(" not in source
