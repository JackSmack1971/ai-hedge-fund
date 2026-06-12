import hashlib
import json
import os
from enum import Enum
from collections import OrderedDict
from pathlib import Path
from typing import Any, List, Tuple

from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langchain_gigachat import GigaChat
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_xai import ChatXAI
from pydantic import BaseModel

from src.config import src_settings


class ModelProvider(str, Enum):
    """Enum for supported LLM providers"""

    ALIBABA = "Alibaba"
    ANTHROPIC = "Anthropic"
    DEEPSEEK = "DeepSeek"
    GOOGLE = "Google"
    GROQ = "Groq"
    META = "Meta"
    MISTRAL = "Mistral"
    OPENAI = "OpenAI"
    OLLAMA = "Ollama"
    OPENROUTER = "OpenRouter"
    GIGACHAT = "GigaChat"
    AZURE_OPENAI = "Azure OpenAI"
    XAI = "xAI"


class LLMModel(BaseModel):
    """Represents an LLM model configuration"""

    display_name: str
    model_name: str
    provider: ModelProvider

    def to_choice_tuple(self) -> Tuple[str, str, str]:
        """Convert to format needed for questionary choices"""
        return (self.display_name, self.model_name, self.provider.value)

    def is_custom(self) -> bool:
        """Check if the model is a Gemini model"""
        return self.model_name == "-"

    def has_json_mode(self) -> bool:
        """Check if the model supports JSON mode"""
        if self.is_deepseek() or self.is_gemini():
            return False
        # Only certain Ollama models support JSON mode
        if self.is_ollama():
            return "llama3" in self.model_name or "neural-chat" in self.model_name
        # OpenRouter models generally support JSON mode
        if self.provider == ModelProvider.OPENROUTER:
            return True
        return True

    def is_deepseek(self) -> bool:
        """Check if the model is a DeepSeek model"""
        return self.model_name.startswith("deepseek")

    def is_gemini(self) -> bool:
        """Check if the model is a Gemini model"""
        return self.model_name.startswith("gemini")

    def is_ollama(self) -> bool:
        """Check if the model is an Ollama model"""
        return self.provider == ModelProvider.OLLAMA


# Load models from JSON file
def load_models_from_json(json_path: str) -> List[LLMModel]:
    """Load models from a JSON file"""
    with open(json_path, "r") as f:
        models_data = json.load(f)

    models = []
    for model_data in models_data:
        # Convert string provider to ModelProvider enum
        provider_enum = ModelProvider(model_data["provider"])
        models.append(
            LLMModel(
                display_name=model_data["display_name"], model_name=model_data["model_name"], provider=provider_enum
            )
        )
    return models


# Get the path to the JSON files
current_dir = Path(__file__).parent
models_json_path = current_dir / "api_models.json"
ollama_models_json_path = current_dir / "ollama_models.json"

# Load available models from JSON
AVAILABLE_MODELS = load_models_from_json(str(models_json_path))

# Load Ollama models from JSON
OLLAMA_MODELS = load_models_from_json(str(ollama_models_json_path))

# Create LLM_ORDER in the format expected by the UI
LLM_ORDER = [model.to_choice_tuple() for model in AVAILABLE_MODELS]

# Create Ollama LLM_ORDER separately
OLLAMA_LLM_ORDER = [model.to_choice_tuple() for model in OLLAMA_MODELS]

_MODEL_CACHE_MAXSIZE = 32
_MODEL_CACHE: OrderedDict[tuple[str, str, tuple[tuple[str, str], ...] | None], Any] = OrderedDict()


def get_model_info(model_name: str, model_provider: str) -> LLMModel | None:
    """Get model information by model_name"""
    all_models = AVAILABLE_MODELS + OLLAMA_MODELS
    return next(
        (model for model in all_models if model.model_name == model_name and model.provider == model_provider), None
    )


def find_model_by_name(model_name: str) -> LLMModel | None:
    """Find a model by its name across all available models."""
    all_models = AVAILABLE_MODELS + OLLAMA_MODELS
    return next((model for model in all_models if model.model_name == model_name), None)


def get_models_list():
    """Get the list of models for API responses."""
    return [
        {"display_name": model.display_name, "model_name": model.model_name, "provider": model.provider.value}
        for model in AVAILABLE_MODELS
    ]


def _build_model(
    model_name: str, model_provider: ModelProvider, api_keys: dict = None
) -> ChatOpenAI | ChatGroq | ChatOllama | GigaChat | None:  # noqa: E501
    if model_provider == ModelProvider.GROQ:
        api_key = src_settings.get_provider_api_key("GROQ", api_keys)
        if not api_key:
            # Print error to console
            print("API Key Error: Please make sure GROQ_API_KEY is set in your .env file or provided via API keys.")
            raise ValueError(
                "Groq API key not found.  Please make sure GROQ_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatGroq(model=model_name, api_key=api_key)
    elif model_provider == ModelProvider.OPENAI:
        # Get and validate API key
        api_key = src_settings.get_provider_api_key("OPENAI", api_keys)
        base_url = src_settings.openai_api_base
        if not api_key:
            # Print error to console
            print("API Key Error: Please make sure OPENAI_API_KEY is set in your .env file or provided via API keys.")
            raise ValueError(
                "OpenAI API key not found.  Please make sure OPENAI_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatOpenAI(model=model_name, api_key=api_key, base_url=base_url)
    elif model_provider == ModelProvider.ANTHROPIC:
        api_key = src_settings.get_provider_api_key("ANTHROPIC", api_keys)
        if not api_key:
            print(
                "API Key Error: Please make sure ANTHROPIC_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "Anthropic API key not found.  Please make sure ANTHROPIC_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatAnthropic(model=model_name, api_key=api_key)
    elif model_provider == ModelProvider.DEEPSEEK:
        api_key = src_settings.get_provider_api_key("DEEPSEEK", api_keys)
        if not api_key:
            print("API Key Error: Please make sure DEEPSEEK_API_KEY is set in your .env file or provided via API keys.")
            raise ValueError(
                "DeepSeek API key not found.  Please make sure DEEPSEEK_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatDeepSeek(model=model_name, api_key=api_key)
    elif model_provider == ModelProvider.GOOGLE:
        api_key = src_settings.get_provider_api_key("GOOGLE", api_keys)
        if not api_key:
            print("API Key Error: Please make sure GOOGLE_API_KEY is set in your .env file or provided via API keys.")
            raise ValueError(
                "Google API key not found.  Please make sure GOOGLE_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
    elif model_provider == ModelProvider.OLLAMA:
        # For Ollama, we use a base URL instead of an API key
        # Check if OLLAMA_HOST is set (for Docker on macOS)
        base_url = src_settings.get_ollama_base_url()
        return ChatOllama(
            model=model_name,
            base_url=base_url,
        )
    elif model_provider == ModelProvider.OPENROUTER:
        api_key = src_settings.get_provider_api_key("OPENROUTER", api_keys)
        if not api_key:
            print(
                "API Key Error: Please make sure OPENROUTER_API_KEY is set in your .env file or provided via API keys."
            )
            raise ValueError(
                "OpenRouter API key not found. Please make sure OPENROUTER_API_KEY is set in your .env file or provided via API keys."
            )

        # Get optional site URL and name for headers
        site_url = src_settings.your_site_url
        site_name = src_settings.your_site_name

        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            model_kwargs={
                "extra_headers": {
                    "HTTP-Referer": site_url,
                    "X-Title": site_name,
                }
            },
        )
    elif model_provider == ModelProvider.XAI:
        api_key = src_settings.get_provider_api_key("XAI", api_keys)
        if not api_key:
            print("API Key Error: Please make sure XAI_API_KEY is set in your .env file or provided via API keys.")
            raise ValueError(
                "xAI API key not found. Please make sure XAI_API_KEY is set in your .env file or provided via API keys."
            )
        return ChatXAI(model=model_name, api_key=api_key)
    elif model_provider == ModelProvider.GIGACHAT:
        if src_settings.gigachat_user or src_settings.gigachat_password:
            return GigaChat(model=model_name)
        else:
            api_key = (
                (api_keys or {}).get("GIGACHAT_API_KEY")
                or src_settings.gigachat_api_key
                or src_settings.gigachat_credentials
            )
            if not api_key:
                print("API Key Error: Please make sure api_keys is set in your .env file or provided via API keys.")
                raise ValueError(
                    "GigaChat API key not found. Please make sure GIGACHAT_API_KEY is set in your .env file or provided via API keys."
                )

            return GigaChat(credentials=api_key, model=model_name)
    elif model_provider == ModelProvider.AZURE_OPENAI:
        # Get and validate API key
        api_key = src_settings.azure_openai_api_key
        if not api_key:
            # Print error to console
            print("API Key Error: Please make sure AZURE_OPENAI_API_KEY is set in your .env file.")
            raise ValueError(
                "Azure OpenAI API key not found.  Please make sure AZURE_OPENAI_API_KEY is set in your .env file."
            )
        # Get and validate Azure Endpoint
        azure_endpoint = src_settings.azure_openai_endpoint
        if not azure_endpoint:
            # Print error to console
            print("Azure Endpoint Error: Please make sure AZURE_OPENAI_ENDPOINT is set in your .env file.")
            raise ValueError(
                "Azure OpenAI endpoint not found.  Please make sure AZURE_OPENAI_ENDPOINT is set in your .env file."
            )
        # get and validate deployment name
        azure_deployment_name = src_settings.azure_openai_deployment_name
        if not azure_deployment_name:
            # Print error to console
            print(
                "Azure Deployment Name Error: Please make sure AZURE_OPENAI_DEPLOYMENT_NAME is set in your .env file."
            )
            raise ValueError(
                "Azure OpenAI deployment name not found.  Please make sure AZURE_OPENAI_DEPLOYMENT_NAME is set in your .env file."
            )
        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment_name,
            api_key=api_key,
            api_version="2024-10-21",
        )


def _fingerprint_api_keys(api_keys: dict | None) -> tuple[tuple[str, str], ...] | None:
    if not api_keys:
        return None

    return tuple(
        sorted(
            (key, hashlib.sha256(value.encode("utf-8")).hexdigest())
            for key, value in api_keys.items()
        )
    )


def _cache_key(model_name: str, provider_str: str, api_keys: dict | None) -> tuple[str, str, tuple[tuple[str, str], ...] | None]:
    return (model_name, provider_str, _fingerprint_api_keys(api_keys))


def clear_model_cache() -> None:
    _MODEL_CACHE.clear()


def _cached_get_model(model_name: str, provider_str: str, api_keys: dict | None):
    """LRU-cached wrapper — one client instance per (model, provider, api_keys fingerprint) tuple."""
    cache_key = _cache_key(model_name, provider_str, api_keys)
    if cache_key in _MODEL_CACHE:
        _MODEL_CACHE.move_to_end(cache_key)
        return _MODEL_CACHE[cache_key]

    return _build_model(model_name, provider_str, api_keys)


def get_model(model_name: str, model_provider, api_keys: dict = None):
    """Return a cached LLM client, reusing instances across repeated call_llm() invocations."""
    provider_str = model_provider.value if hasattr(model_provider, "value") else str(model_provider)
    cache_key = _cache_key(model_name, provider_str, api_keys)
    if cache_key in _MODEL_CACHE:
        _MODEL_CACHE.move_to_end(cache_key)
        return _MODEL_CACHE[cache_key]

    model = _cached_get_model(model_name, provider_str, api_keys)
    _MODEL_CACHE[cache_key] = model
    if len(_MODEL_CACHE) > _MODEL_CACHE_MAXSIZE:
        _MODEL_CACHE.popitem(last=False)
    return model
