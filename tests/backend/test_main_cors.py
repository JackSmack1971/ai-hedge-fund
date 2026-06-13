"""Tests for backend CORS configuration."""

from fastapi.middleware.cors import CORSMiddleware

from app.backend.main import app


def test_cors_config_uses_explicit_methods_and_headers():
    cors_middleware = next(middleware for middleware in app.user_middleware if middleware.cls is CORSMiddleware)

    assert cors_middleware.kwargs["allow_credentials"] is False
    assert cors_middleware.kwargs["allow_methods"] == ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    assert cors_middleware.kwargs["allow_headers"] == ["Authorization", "Content-Type", "Accept"]
