"""Tests for src/llm/models.py — provider routing and model configuration."""

import os
from unittest.mock import patch

import pytest

from src.llm.models import (
    AVAILABLE_MODELS,
    _MODEL_CACHE,
    find_model_by_name,
    clear_model_cache,
    get_model,
    get_model_info,
    LLMModel,
    ModelProvider,
)


class TestModelProvider:
    def test_enum_values_exist(self):
        assert ModelProvider.ANTHROPIC == "Anthropic"
        assert ModelProvider.OPENAI == "OpenAI"
        assert ModelProvider.GROQ == "Groq"
        assert ModelProvider.OLLAMA == "Ollama"

    def test_string_coercion(self):
        assert ModelProvider("Anthropic") == ModelProvider.ANTHROPIC


class TestLLMModel:
    def test_has_json_mode_anthropic(self):
        m = LLMModel(display_name="Claude", model_name="claude-3-5-sonnet-20241022", provider=ModelProvider.ANTHROPIC)
        assert m.has_json_mode() is True

    def test_has_json_mode_ollama_llama3(self):
        m = LLMModel(display_name="Llama3", model_name="llama3:latest", provider=ModelProvider.OLLAMA)
        assert m.has_json_mode() is True

    def test_has_json_mode_ollama_non_llama(self):
        m = LLMModel(display_name="Mistral", model_name="mistral:latest", provider=ModelProvider.OLLAMA)
        assert m.has_json_mode() is False

    def test_is_deepseek(self):
        m = LLMModel(display_name="DeepSeek", model_name="deepseek-chat", provider=ModelProvider.DEEPSEEK)
        assert m.is_deepseek() is True
        assert m.has_json_mode() is False

    def test_is_ollama(self):
        m = LLMModel(display_name="Ollama", model_name="llama3", provider=ModelProvider.OLLAMA)
        assert m.is_ollama() is True

    def test_is_not_ollama(self):
        m = LLMModel(display_name="GPT", model_name="gpt-4o", provider=ModelProvider.OPENAI)
        assert m.is_ollama() is False


class TestGetModelInfo:
    def test_returns_none_for_unknown_model(self):
        result = get_model_info("nonexistent-model-xyz", "UnknownProvider")
        assert result is None

    def test_returns_model_for_known_openai(self):
        openai_model = next((m for m in AVAILABLE_MODELS if m.provider == ModelProvider.OPENAI), None)
        if openai_model:
            result = get_model_info(openai_model.model_name, openai_model.provider.value)
            assert result is not None
            assert result.provider == ModelProvider.OPENAI

    def test_returns_model_for_known_anthropic(self):
        anthropic_model = next((m for m in AVAILABLE_MODELS if m.provider == ModelProvider.ANTHROPIC), None)
        if anthropic_model:
            result = get_model_info(anthropic_model.model_name, anthropic_model.provider.value)
            assert result is not None
            assert result.provider == ModelProvider.ANTHROPIC


class TestFindModelByName:
    def test_finds_existing_model(self):
        if AVAILABLE_MODELS:
            model_name = AVAILABLE_MODELS[0].model_name
            result = find_model_by_name(model_name)
            assert result is not None
            assert result.model_name == model_name

    def test_returns_none_for_unknown(self):
        result = find_model_by_name("definitely-not-a-real-model-name-xyz")
        assert result is None


class TestGetModel:
    def setup_method(self):
        clear_model_cache()

    def test_missing_openai_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI"):
                get_model("gpt-4o", ModelProvider.OPENAI, api_keys={})

    def test_missing_anthropic_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Anthropic"):
                get_model("claude-3-5-sonnet-20241022", ModelProvider.ANTHROPIC, api_keys={})

    def test_missing_groq_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Groq"):
                get_model("llama-3.1-70b-versatile", ModelProvider.GROQ, api_keys={})

    @patch("src.llm.models.ChatOpenAI")
    def test_openai_client_returned(self, mock_chat_openai):
        mock_chat_openai.return_value = "mock-openai-client"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            result = get_model("gpt-4o", ModelProvider.OPENAI)
        mock_chat_openai.assert_called_once()
        assert result == "mock-openai-client"

    @patch("src.llm.models.ChatAnthropic")
    def test_anthropic_client_returned(self, mock_chat_anthropic):
        mock_chat_anthropic.return_value = "mock-anthropic-client"
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = get_model("claude-3-5-sonnet-20241022", ModelProvider.ANTHROPIC)
        mock_chat_anthropic.assert_called_once()
        assert result == "mock-anthropic-client"

    @patch("src.llm.models.ChatOllama")
    def test_ollama_client_no_key_required(self, mock_chat_ollama):
        mock_chat_ollama.return_value = "mock-ollama-client"
        with patch.dict(os.environ, {}, clear=True):
            result = get_model("llama3", ModelProvider.OLLAMA)
        mock_chat_ollama.assert_called_once()
        assert result == "mock-ollama-client"

    @patch("src.llm.models.ChatOpenAI")
    def test_api_keys_dict_takes_precedence_over_env(self, mock_chat_openai):
        mock_chat_openai.return_value = "client"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            get_model("gpt-4o", ModelProvider.OPENAI, api_keys={"OPENAI_API_KEY": "dict-key"})
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs.get("api_key") == "dict-key"

    @patch("src.llm.models.ChatOpenAI")
    def test_cache_key_omits_plaintext_api_keys(self, mock_chat_openai):
        mock_chat_openai.return_value = "client"
        secret = "super-secret-key"

        with patch.dict(os.environ, {"OPENAI_API_KEY": secret}):
            get_model("gpt-4o", ModelProvider.OPENAI, api_keys={"OPENAI_API_KEY": secret})

        cache_key = next(iter(_MODEL_CACHE.keys()))
        assert cache_key[2] is not None
        hashed_key = dict(cache_key[2])["OPENAI_API_KEY"]
        assert hashed_key != secret
        assert len(hashed_key) == 64

    @patch("src.llm.models.ChatOpenAI")
    def test_key_rotation_bypasses_previous_cache_entry(self, mock_chat_openai):
        mock_chat_openai.return_value = "client"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "key-one"}):
            get_model("gpt-4o", ModelProvider.OPENAI, api_keys={"OPENAI_API_KEY": "key-one"})

        with patch.dict(os.environ, {"OPENAI_API_KEY": "key-two"}):
            get_model("gpt-4o", ModelProvider.OPENAI, api_keys={"OPENAI_API_KEY": "key-two"})

        assert mock_chat_openai.call_count == 2

    def test_unknown_provider_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Unknown model provider"):
                get_model("gpt-4o", "DefinitelyNotAProvider", api_keys={})
