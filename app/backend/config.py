"""Shared application settings for backend modules."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    backend_api_token: str | None = None
    database_encryption_key: str | None = None
    auto_create_tables: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"

    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod", "staging"}

    def get_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def get_backend_settings() -> BackendSettings:
    return BackendSettings()


class _SettingsProxy:
    def __init__(self, factory):
        self._factory = factory

    def __getattr__(self, item):
        return getattr(self._factory(), item)

    def __call__(self):
        return self._factory()


backend_settings = _SettingsProxy(get_backend_settings)
