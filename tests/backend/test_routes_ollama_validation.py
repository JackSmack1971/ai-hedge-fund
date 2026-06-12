"""Tests for Ollama model-name validation."""

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from unittest.mock import AsyncMock, patch

    with patch(
        "app.backend.services.ollama_service.ollama_service.check_ollama_status",
        new=AsyncMock(return_value={"installed": True, "running": True, "available_models": [], "server_url": ""}),
    ):
        from app.backend.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_download_model_rejects_path_like_name(client: TestClient):
    response = client.post("/ollama/models/download", json={"model_name": "../../../etc/passwd"})

    assert response.status_code == 422


def test_delete_model_rejects_path_like_name(client: TestClient):
    bad_model_name = quote("bad model name", safe="")
    response = client.delete(f"/ollama/models/{bad_model_name}")

    assert response.status_code == 422
