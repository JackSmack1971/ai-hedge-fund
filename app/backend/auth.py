"""Bearer-token authentication for the backend API.

Routes are protected by comparing the ``Authorization: Bearer <token>`` header
against the ``BACKEND_API_TOKEN`` environment variable:

- ``BACKEND_API_TOKEN`` set: every protected route requires a matching token.
- ``BACKEND_API_TOKEN`` unset in development (the default ``ENVIRONMENT``):
  authentication is disabled so local workflows keep working.
- ``BACKEND_API_TOKEN`` unset with ``ENVIRONMENT=production``: fail closed —
  all protected routes return 503 until a token is configured.
- SSE endpoints can also accept the token as a ``?token=...`` query parameter
  for browser-native EventSource clients that cannot send Authorization headers.
"""

import logging
import os
import secrets

from fastapi import HTTPException, Query, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

_PRODUCTION_ENVIRONMENTS = {"production", "prod"}


def _is_production() -> bool:
    return os.environ.get("ENVIRONMENT", "development").strip().lower() in _PRODUCTION_ENVIRONMENTS


async def verify_backend_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> None:
    """FastAPI dependency enforcing the BACKEND_API_TOKEN bearer token."""
    expected = os.environ.get("BACKEND_API_TOKEN")

    if not expected:
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="BACKEND_API_TOKEN is not configured; refusing requests in production",
            )
        return

    if credentials is None or not secrets.compare_digest(credentials.credentials.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _matches_expected_token(expected: str, provided_tokens: list[str | None]) -> bool:
    """Return True when any provided token matches the configured token."""
    expected_bytes = expected.encode()
    return any(
        provided_token is not None
        and secrets.compare_digest(provided_token.encode(), expected_bytes)
        for provided_token in provided_tokens
    )


async def verify_backend_token_or_query(
    token: str | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> None:
    """FastAPI dependency that accepts bearer auth or a `token` query parameter.

    Browser-native EventSource clients cannot send Authorization headers, so
    SSE endpoints can use this dependency to accept `?token=...` instead.
    """
    expected = os.environ.get("BACKEND_API_TOKEN")

    if not expected:
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="BACKEND_API_TOKEN is not configured; refusing requests in production",
            )
        return

    if _matches_expected_token(expected, [credentials.credentials if credentials else None, token]):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )
