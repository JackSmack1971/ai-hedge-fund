"""Bearer-token authentication for the backend API.

Routes are protected by comparing the ``Authorization: Bearer <token>`` header
against the ``BACKEND_API_TOKEN`` environment variable:

- ``BACKEND_API_TOKEN`` set: every protected route requires a matching token.
- ``BACKEND_API_TOKEN`` unset in development (the default ``ENVIRONMENT``):
  authentication is disabled so local workflows keep working.
- ``BACKEND_API_TOKEN`` unset with ``ENVIRONMENT=production``: fail closed —
  all protected routes return 503 until a token is configured.
"""

import logging
import os
import secrets

from fastapi import HTTPException, Security, status
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
