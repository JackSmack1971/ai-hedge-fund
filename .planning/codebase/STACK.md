# Technology Stack

**Analysis Date:** 2026-06-09

## Languages

**Primary:**
- Python 3.11 - Backend service, agent logic, backtesting engine, and CLI entry points.
- TypeScript 5.3 - Frontend React application code.

**Secondary:**
- JavaScript - Build scripts, linting/formatting configs (Vite, Tailwind, ESLint, PostCSS).

## Runtime

**Environment:**
- Python 3.11+ - Executed locally or via Docker containers.
- Node.js 20.x (LTS) - For compiling and running the Vite/React frontend.

**Package Managers:**
- Poetry 1.7.1 - Backend package management. Lockfile: `poetry.lock` present.
- npm 10.x - Frontend package management. Lockfile: `package-lock.json` present.

## Frameworks

**Core:**
- FastAPI 0.104.0 - Backend REST API server and SSE streaming.
- LangGraph 0.3.0 - Orchestrates the multi-agent DAG workflow.
- LangChain 0.3.7 - Core LLM abstraction layer and provider integrations.
- React 18.2 - Frontend user interface.
- Vite 5.0.12 - Frontend build tool and development server.

**Testing:**
- Pytest 8.3 - Python test runner.
- Pytest-Cov - Coverage reporting.
- Pytest-Asyncio - Async test support.
- ESLint 8.56.0 - Frontend linting tool.

**Build/Dev:**
- Black 24.0 - Python code formatting.
- Isort 5.12.0 - Python import sorting.
- Flake8 6.1.0 - Python code linting.
- Mypy 1.10 - Python static type checking.
- Bandit 1.7 - Python security scanning.
- Uvicorn 0.22.0+ - ASGI server running FastAPI.

## Key Dependencies

**Critical:**
- `langchain-openai` 0.3.5 - OpenAI models (GPT-4o, etc.).
- `langchain-anthropic` 0.3.5 - Anthropic models (Claude 3.5 Sonnet, etc.).
- `langchain-google-genai` 2.0.11 - Google Gemini models.
- `langchain-groq` 0.2.3 - Groq models.
- `langchain-deepseek` 0.1.2 - DeepSeek models.
- `langchain-ollama` 0.3.6 - Local Ollama model integration.
- `sqlalchemy` 2.0.22 - SQL database ORM.
- `alembic` 1.12.0 - Database migration tool.
- `@xyflow/react` 12.5.1 - Frontend React Flow graph visualizer.
- `celery` 5.4.0 - Distributed task queue (async flow-runs).

**Infrastructure:**
- `pandas` 2.1.0 - Data frames for financial data manipulation.
- `numpy` >=2.0,<3 - Numerical computation.
- `requests` - HTTP client for financial APIs.
- `httpx` 0.27.0 - Async HTTP client for backend and tests.
- `redis` 5.0.0+ - Celery message broker.
- `shadcn-ui` 0.9.5 - Accessible frontend components styled with Tailwind.

## Configuration

**Environment:**
- `.env` / `.env.example` - Backend and API secrets (e.g. `OPENAI_API_KEY`, `FINANCIAL_DATASETS_API_KEY`).
- Configured via `python-dotenv` at runtime.

**Build:**
- `pyproject.toml` - Full Poetry setup, Pytest options, Black line limit (120), Mypy settings.
- `app/frontend/vite.config.ts` - Vite configuration for dev server proxy and react plugin.
- `app/frontend/tailwind.config.ts` - TailwindCSS 3.4 configuration.

## Platform Requirements

**Development:**
- Windows/macOS/Linux with Python 3.11+ and Node.js 20+.
- Financial Datasets API key for stock price queries.

**Production:**
- Docker / Docker Compose - Multi-container setup (FastAPI, Redis, Celery worker, Ollama).
- SQLite db (`app/backend/hedge_fund.db`) or cloud PostgreSQL target via `DATABASE_URL`.

---

*Stack analysis: 2026-06-09*
*Update after major dependency changes*
