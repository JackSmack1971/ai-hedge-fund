"""Shared application settings for src modules."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class SrcSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    financial_datasets_api_key: str | None = None
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    openai_api_base: str | None = None
    anthropic_api_key: str | None = None
    deepseek_api_key: str | None = None
    google_api_key: str | None = None
    ollama_host: str = "localhost"
    ollama_base_url: str | None = None
    openrouter_api_key: str | None = None
    your_site_url: str = "https://github.com/virattt/ai-hedge-fund"
    your_site_name: str = "AI Hedge Fund"
    xai_api_key: str | None = None
    gigachat_user: str | None = None
    gigachat_password: str | None = None
    gigachat_api_key: str | None = None
    gigachat_credentials: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment_name: str | None = None

    def get_ollama_base_url(self) -> str:
        return self.ollama_base_url or f"http://{self.ollama_host}:11434"

    def get_provider_api_key(self, provider: str, api_keys: dict | None = None) -> str | None:
        provider_key_map = {
            "GROQ": "GROQ_API_KEY",
            "OPENAI": "OPENAI_API_KEY",
            "ANTHROPIC": "ANTHROPIC_API_KEY",
            "DEEPSEEK": "DEEPSEEK_API_KEY",
            "GOOGLE": "GOOGLE_API_KEY",
            "OPENROUTER": "OPENROUTER_API_KEY",
            "XAI": "XAI_API_KEY",
        }
        provider_attr_map = {
            "GROQ": self.groq_api_key,
            "OPENAI": self.openai_api_key,
            "ANTHROPIC": self.anthropic_api_key,
            "DEEPSEEK": self.deepseek_api_key,
            "GOOGLE": self.google_api_key,
            "OPENROUTER": self.openrouter_api_key,
            "XAI": self.xai_api_key,
        }

        provider_name = provider.upper()
        provider_key = provider_key_map.get(provider_name)
        if api_keys and provider_key and api_keys.get(provider_key):
            return api_keys[provider_key]
        return provider_attr_map.get(provider_name)


def get_src_settings() -> SrcSettings:
    return SrcSettings()


class _SettingsProxy:
    def __init__(self, factory):
        self._factory = factory

    def __getattr__(self, item):
        return getattr(self._factory(), item)

    def __call__(self):
        return self._factory()


src_settings = _SettingsProxy(get_src_settings)
