"""Tests for src/utils/ollama.py — availability checks and model listing."""

from unittest.mock import Mock, patch

import pytest

from src.utils.ollama import (
    _get_ollama_base_url,
    _get_ollama_endpoint,
    get_locally_available_models,
    is_ollama_server_running,
)


class TestOllamaBaseUrl:
    def test_default_url(self):
        import os

        with patch.dict(os.environ, {}, clear=True):
            url = _get_ollama_base_url()
            assert "localhost" in url or "11434" in url

    def test_custom_url_from_env(self):
        import os

        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://myhost:11434"}):
            url = _get_ollama_base_url()
            assert url == "http://myhost:11434"

    def test_trailing_slash_stripped(self):
        import os

        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434/"}):
            url = _get_ollama_base_url()
            assert not url.endswith("/")

    def test_endpoint_construction(self):
        url = _get_ollama_endpoint("/api/tags")
        assert url.endswith("/api/tags")


class TestIsOllamaServerRunning:
    @patch("src.utils.ollama.requests.get")
    def test_returns_true_when_server_responds(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        assert is_ollama_server_running() is True

    @patch("src.utils.ollama.requests.get")
    def test_returns_false_on_connection_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("refused")
        assert is_ollama_server_running() is False

    @patch("src.utils.ollama.requests.get")
    def test_returns_false_on_timeout(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("timeout")
        assert is_ollama_server_running() is False


class TestGetLocallyAvailableModels:
    @patch("src.utils.ollama.requests.get")
    def test_parses_model_list(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:latest"},
                {"name": "mistral:latest"},
            ]
        }
        mock_get.return_value = mock_response
        models = get_locally_available_models()
        assert isinstance(models, list)
        assert "llama3:latest" in models

    @patch("src.utils.ollama.requests.get")
    def test_returns_empty_on_connection_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError()
        models = get_locally_available_models()
        assert models == []

    @patch("src.utils.ollama.requests.get")
    def test_returns_empty_on_bad_status(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        models = get_locally_available_models()
        assert models == []
