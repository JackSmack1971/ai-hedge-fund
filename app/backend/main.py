import logging
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.database.connection import engine
from app.backend.database.models import Base
from app.backend.config import backend_settings
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
    return backend_settings.auto_create_tables


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

# Configure CORS — override via CORS_ORIGINS env var (comma-separated) for non-local deployments
_cors_origins = backend_settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)
