"""Shared application settings for backend modules."""

import os


class BackendSettings:
    """Centralized access to backend environment variables."""

    @property
    def environment(self) -> str:
        return os.environ.get("ENVIRONMENT", "development")

    @property
    def backend_api_token(self) -> str | None:
        return os.environ.get("BACKEND_API_TOKEN")

    @property
    def database_encryption_key(self) -> str | None:
        return os.environ.get("DATABASE_ENCRYPTION_KEY")

    @property
    def auto_create_tables(self) -> bool:
        return os.environ.get("AUTO_CREATE_TABLES", "true").strip().lower() in {"1", "true", "yes"}

    @property
    def cors_origins(self) -> str:
        return os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    @property
    def database_url(self) -> str | None:
        return os.environ.get("DATABASE_URL")

    @property
    def redis_url(self) -> str:
        return os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod", "staging"}

    def get_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


backend_settings = BackendSettings()
