"""Tests that the Ollama SSE endpoint honors the configured CORS policy instead of a hardcoded wildcard (#23)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _mock_ollama_running():
    return patch(
        "app.backend.routes.ollama.ollama_service.check_ollama_status",
        new=AsyncMock(return_value={"installed": True, "running": True}),
    )


def _mock_progress_stream():
    async def fake_stream(model_name):
        yield "data: {}\n\n"

    return patch(
        "app.backend.routes.ollama.ollama_service.download_model_with_progress",
        side_effect=fake_stream,
    )


def test_progress_endpoint_has_no_wildcard_cors(test_app: TestClient):
    with _mock_ollama_running(), _mock_progress_stream():
        response = test_app.post(
            "/ollama/models/download/progress",
            json={"model_name": "llama3"},
            headers={"Origin": "https://evil.example.com"},
        )

    assert response.status_code == 200, response.text
    acao = response.headers.get("access-control-allow-origin")
    assert acao != "*", "wildcard Access-Control-Allow-Origin must not be hardcoded"
    assert acao != "https://evil.example.com", "disallowed origin must not be reflected"


def test_progress_endpoint_allows_configured_origin(test_app: TestClient):
    allowed_origin = "http://localhost:5173"  # default in CORS_ORIGINS
    with _mock_ollama_running(), _mock_progress_stream():
        response = test_app.post(
            "/ollama/models/download/progress",
            json={"model_name": "llama3"},
            headers={"Origin": allowed_origin},
        )

    assert response.status_code == 200, response.text
    assert response.headers.get("access-control-allow-origin") == allowed_origin
