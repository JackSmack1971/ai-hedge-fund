"""Bearer-token authentication for the backend API.

Routes are protected by comparing the ``Authorization: Bearer <token>`` header
against the ``BACKEND_API_TOKEN`` environment variable:

- ``BACKEND_API_TOKEN`` set: every protected route requires a matching token.
- ``BACKEND_API_TOKEN`` unset: authentication fails closed by default.
- ``DISABLE_AUTH=true``: explicit local-development bypass only.
"""

import logging
import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


def _is_auth_disabled() -> bool:
    return os.environ.get("DISABLE_AUTH", "").strip().lower() in {"1", "true", "yes"}


async def verify_backend_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> None:
    """FastAPI dependency enforcing the BACKEND_API_TOKEN bearer token."""
    expected = os.environ.get("BACKEND_API_TOKEN")

    if not expected:
        if _is_auth_disabled():
            return
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="BACKEND_API_TOKEN is not configured; set DISABLE_AUTH=true only for local development",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials is None or not secrets.compare_digest(credentials.credentials.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
