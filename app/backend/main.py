import logging
import time
from contextlib import asynccontextmanager
from collections import defaultdict, deque
from importlib.metadata import PackageNotFoundError, version
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.backend.database.connection import engine
from app.backend.database.models import Base
from app.backend.config import backend_settings
from app.backend.encryption import EncryptionKeyMissingError
from app.backend.repositories.api_key_repository import ApiKeyRepository
from app.backend.routes import api_router
from app.backend.services.ollama_service import ollama_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_hedge_fund_run_request_times: dict[str, deque[float]] = defaultdict(deque)
_hedge_fund_run_lock = Lock()
_rate_limit_window_seconds = 60

# Single source of truth for the version is pyproject.toml ([tool.poetry] version)
try:
    APP_VERSION = version("ai-hedge-fund")
except PackageNotFoundError:  # running from source without an installed package
    APP_VERSION = "0.0.0+unknown"


def _auto_create_tables_enabled() -> bool:
    return backend_settings.auto_create_tables


def _hedge_fund_run_rate_limit() -> int:
    return backend_settings.hedge_fund_run_rate_limit_per_minute


async def _log_ollama_status() -> None:
    """Check Ollama availability and log the result."""
    try:
        logger.info("Checking Ollama availability...")
        status = await ollama_service.check_ollama_status()

        if status["installed"]:
            if status["running"]:
                logger.info(f"✓ Ollama is installed and running at {status['server_url']}")
                if status["available_models"]:
                    logger.info(f"✓ Available models: {', '.join(status['available_models'])}")
                else:
                    logger.info("ℹ No models are currently downloaded")
            else:
                logger.info("ℹ Ollama is installed but not running")
                logger.info("ℹ You can start it from the Settings page or manually with 'ollama serve'")
        else:
            logger.info("ℹ Ollama is not installed. Install it to use local models.")
            logger.info("ℹ Visit https://ollama.com to download and install Ollama")

    except Exception as e:
        logger.warning(f"Could not check Ollama status: {e}")
        logger.info("ℹ Ollama integration is available if you install it later")


def _reencrypt_plaintext_api_keys_on_startup() -> None:
    """Warn about legacy plaintext API keys and re-encrypt them when possible."""
    from sqlalchemy.exc import OperationalError

    from app.backend.database.connection import SessionLocal

    db = SessionLocal()
    try:
        repo = ApiKeyRepository(db)
        migrated = repo.reencrypt_plaintext_keys()
        if migrated:
            logger.warning("Re-encrypted %s legacy plaintext API key row(s) at startup", migrated)
    except EncryptionKeyMissingError as exc:
        logger.warning("Skipped API key plaintext migration at startup: %s", exc)
    except OperationalError:
        # Tables may not exist yet (e.g. test environments that haven't run migrations).
        logger.debug("Skipped API key plaintext migration: schema not ready")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev/test bootstrap only: Alembic migrations (alembic upgrade head) are the
    # authoritative schema mechanism. Keep AUTO_CREATE_TABLES=false in deployments
    # that run migrations, since create_all never applies column/index changes.
    if _auto_create_tables_enabled():
        Base.metadata.create_all(bind=engine)
    _reencrypt_plaintext_api_keys_on_startup()
    await _log_ollama_status()
    yield


app = FastAPI(
    title="AI Hedge Fund API", description="Backend API for AI Hedge Fund", version=APP_VERSION, lifespan=lifespan
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")
    if response.headers.get("content-type", "").startswith("text/event-stream"):
        response.headers.setdefault("X-Accel-Buffering", "no")
    return response


@app.middleware("http")
async def rate_limit_hedge_fund_run(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/hedge-fund/run":
        client_host = request.client.host if request.client else "unknown"
        now = time.monotonic()
        limit = _hedge_fund_run_rate_limit()

        with _hedge_fund_run_lock:
            request_times = _hedge_fund_run_request_times[client_host]
            while request_times and now - request_times[0] >= _rate_limit_window_seconds:
                request_times.popleft()
            if len(request_times) >= limit:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            request_times.append(now)

    return await call_next(request)

# Configure CORS — override via CORS_ORIGINS env var (comma-separated) for non-local deployments
_cors_origins = backend_settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Include all routes
app.include_router(api_router)
