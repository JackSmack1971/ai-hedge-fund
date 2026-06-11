import logging
import os
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.backend.database.connection import engine
from app.backend.database.models import Base
from app.backend.routes import api_router
from app.backend.services.ollama_service import ollama_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Single source of truth for the version is pyproject.toml ([tool.poetry] version)
try:
    APP_VERSION = version("ai-hedge-fund")
except PackageNotFoundError:  # running from source without an installed package
    APP_VERSION = "0.0.0+unknown"


def _auto_create_tables_enabled() -> bool:
    return os.environ.get("AUTO_CREATE_TABLES", "true").strip().lower() in {"1", "true", "yes"}


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev/test bootstrap only: Alembic migrations (alembic upgrade head) are the
    # authoritative schema mechanism. Set AUTO_CREATE_TABLES=false in deployments
    # that run migrations, since create_all never applies column/index changes.
    if _auto_create_tables_enabled():
        Base.metadata.create_all(bind=engine)
    await _log_ollama_status()
    yield


app = FastAPI(
    title="AI Hedge Fund API", description="Backend API for AI Hedge Fund", version=APP_VERSION, lifespan=lifespan
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 500:
        logger.exception("Unexpected HTTPException in %s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": "An internal error occurred"})

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception in %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred"})

# Configure CORS — override via CORS_ORIGINS env var (comma-separated) for non-local deployments
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)
