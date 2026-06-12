"""Shared application settings for src modules."""

import os


class SrcSettings:
    """Centralized access to src environment variables."""

    @property
    def financial_datasets_api_key(self) -> str | None:
        return os.environ.get("FINANCIAL_DATASETS_API_KEY")

    @property
    def groq_api_key(self) -> str | None:
        return os.environ.get("GROQ_API_KEY")

    @property
    def openai_api_key(self) -> str | None:
        return os.environ.get("OPENAI_API_KEY")

    @property
    def openai_api_base(self) -> str | None:
        return os.environ.get("OPENAI_API_BASE")

    @property
    def anthropic_api_key(self) -> str | None:
        return os.environ.get("ANTHROPIC_API_KEY")

    @property
    def deepseek_api_key(self) -> str | None:
        return os.environ.get("DEEPSEEK_API_KEY")

    @property
    def google_api_key(self) -> str | None:
        return os.environ.get("GOOGLE_API_KEY")

    @property
    def ollama_host(self) -> str:
        return os.environ.get("OLLAMA_HOST", "localhost")

    @property
    def ollama_base_url(self) -> str | None:
        return os.environ.get("OLLAMA_BASE_URL")

    @property
    def openrouter_api_key(self) -> str | None:
        return os.environ.get("OPENROUTER_API_KEY")

    @property
    def your_site_url(self) -> str:
        return os.environ.get("YOUR_SITE_URL", "https://github.com/virattt/ai-hedge-fund")

    @property
    def your_site_name(self) -> str:
        return os.environ.get("YOUR_SITE_NAME", "AI Hedge Fund")

    @property
    def xai_api_key(self) -> str | None:
        return os.environ.get("XAI_API_KEY")

    @property
    def gigachat_user(self) -> str | None:
        return os.environ.get("GIGACHAT_USER")

    @property
    def gigachat_password(self) -> str | None:
        return os.environ.get("GIGACHAT_PASSWORD")

    @property
    def gigachat_api_key(self) -> str | None:
        return os.environ.get("GIGACHAT_API_KEY")

    @property
    def gigachat_credentials(self) -> str | None:
        return os.environ.get("GIGACHAT_CREDENTIALS")

    @property
    def azure_openai_api_key(self) -> str | None:
        return os.environ.get("AZURE_OPENAI_API_KEY")

    @property
    def azure_openai_endpoint(self) -> str | None:
        return os.environ.get("AZURE_OPENAI_ENDPOINT")

    @property
    def azure_openai_deployment_name(self) -> str | None:
        return os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

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


src_settings = SrcSettings()
