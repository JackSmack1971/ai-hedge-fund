# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

An educational AI-powered hedge fund simulation. Multiple LLM-backed agents (modeled after famous investors) analyze tickers in parallel via a LangGraph DAG, then a risk manager and portfolio manager synthesize their signals into trade decisions. It has two modes: a CLI entry point (`src/main.py`) and a full-stack web app (`app/`).

**Not for real trading.** Financial data from Financial Datasets API; free tier covers AAPL, GOOGL, MSFT, NVDA, TSLA.

---

## Commands

### Python (Poetry, Python 3.11+)

```bash
poetry install                  # install all deps (runtime + dev)
poetry run pytest               # full test suite with coverage (42% gate)
poetry run pytest tests/backend -q            # backend tests only
poetry run pytest tests/agents/test_all_agents.py -k "buffett" -v  # single test
poetry run black . && poetry run isort .      # format
poetry run flake8 src/ app/ tests/ --max-line-length=120  # lint
poetry run mypy src/ app/backend/ --ignore-missing-imports --no-strict-optional
poetry run bandit -r src/ app/backend/ -ll -x tests/      # security scan
```

### CLI entry points

```bash
poetry run python src/main.py --ticker AAPL,MSFT --start-date 2024-01-01 --end-date 2024-12-31
poetry run python src/backtester.py --ticker AAPL --start-date 2024-01-01 --end-date 2024-12-31
```

### Web app (FastAPI backend + React frontend)

```bash
# Backend (from repo root)
poetry run uvicorn app.backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd app/frontend && npm ci && npm run dev    # http://localhost:5173
cd app/frontend && npm run lint
cd app/frontend && npm run build
```

### Tests require fake API keys

```bash
OPENAI_API_KEY=test-key ANTHROPIC_API_KEY=test-key FINANCIAL_DATASETS_API_KEY=test-key \
  poetry run pytest tests/backend/ -v --no-cov
```

### Docker

```bash
docker-compose up hedge-fund                  # CLI default run
docker-compose up --profile embedded-ollama   # include local Ollama
docker-compose up backtester
```

---

## Architecture

### Core engine (`src/`)

The LangGraph workflow is assembled in `src/main.py::create_workflow()` and `src/backtester.py`. The graph shape is:

```
START → [analyst agents in parallel] → risk_management_agent → portfolio_management_agent → END
```

**`src/graph/state.py`** — defines `AgentState` (the typed dict flowing through the graph):
- `messages`: appended with `operator.add`
- `data` and `metadata`: merged with a custom `merge_dicts` (last-write-wins per key)

**`src/agents/`** — one file per analyst (e.g., `warren_buffett.py`, `cathie_wood.py`). Each agent function receives `AgentState`, calls `call_model()` from `src/utils/llm.py`, and returns a partial state update. `portfolio_manager.py` and `risk_manager.py` are the final two nodes.

**`src/utils/analysts.py`** — `get_analyst_nodes()` returns a `{key: (node_name, fn)}` dict; this is the registry for wiring analysts into the graph and for CLI/UI selection.

**`src/llm/models.py`** — provider abstraction; `get_model(name, provider)` returns a LangChain chat model. Supported: OpenAI, Anthropic, Groq, DeepSeek, Google, xAI, Azure OpenAI, Ollama.

**`src/data/`** — financial data fetching and `cache.py` (in-memory cache keyed by ticker to avoid duplicate API calls within one run).

**`src/backtesting/`** — standalone engine: `engine.py` drives date iteration, `portfolio.py` tracks positions, `metrics.py` computes Sharpe/drawdown, `trader.py` converts signals to orders.

### Web app (`app/`)

**Backend** — FastAPI in `app/backend/main.py`. Schema is owned by Alembic migrations (`app/backend/alembic/`; run `alembic upgrade head` on deploy). As a dev/test convenience the lifespan handler also runs `Base.metadata.create_all()` unless `AUTO_CREATE_TABLES=false`; `create_all` only adds missing tables and never applies column/index changes. Key routes:

| Route | File | Notes |
|---|---|---|
| `POST /hedge-fund/run` | `routes/hedge_fund.py` | Streams SSE; calls the same `run_hedge_fund()` as CLI |
| `POST /flows`, `GET /flows/{id}` | `routes/flows.py` | Saved flow configurations |
| `POST /flow-runs/{id}` | `routes/flow_runs.py` | Async execution via Celery |
| `POST /api-keys` | `routes/api_keys.py` | Encrypted DB storage; needs `DATABASE_ENCRYPTION_KEY` |
| `GET /language-models` | `routes/language_models.py` | Available LLM list |

Repository pattern: `app/backend/repositories/` holds DB access; `app/backend/services/` holds business logic (no FastAPI imports).

**Frontend** — React 18 + Vite 5 + TypeScript. Uses `@xyflow/react` for the agent graph visualization, shadcn/ui + Radix primitives, TailwindCSS 3. Source in `app/frontend/src/`.

**Async tasks** — Celery + Redis (`REDIS_URL` env var). Worker defined in `app/backend/tasks/`.

### Test layout

```
tests/
├── agents/       # agent logic, including regression tests per investor
├── backend/      # FastAPI routes and services (uses httpx AsyncClient + mocks)
├── backtesting/  # integration tests with mocked financial data
├── llm/          # model selection/provider logic
├── data/         # caching and data-fetch mocks
└── cli/          # CLI argument parsing
```

Coverage is measured over `src/` and `app/backend/` (not frontend). Gate is 42%.

---

## Environment Variables

Copy `.env.example` to `.env`. Key vars:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Primary LLM provider |
| `ANTHROPIC_API_KEY` | Claude models |
| `GROQ_API_KEY` | Fast inference |
| `FINANCIAL_DATASETS_API_KEY` | Market data |
| `BACKEND_API_TOKEN` | Protects backend routes (web app) |
| `DATABASE_ENCRYPTION_KEY` | Encrypts stored API keys |
| `REDIS_URL` | Celery broker (default `redis://localhost:6379/0`) |
| `CORS_ORIGINS` | Comma-separated allowed origins (default: localhost:5173) |

---

## Code Style

- **Line length**: 120 (Black config; flake8 `--max-line-length=120`)
- **Formatting**: Black + isort (`profile = "black"`)
- **Mypy**: non-strict (`strict = false`, `ignore_missing_imports = true`) — incremental tightening in progress
- **Flake8**: ~687 violations still pending cleanup; CI runs with `continue-on-error: true` on the lint step
- **Commits**: Conventional Commits style (`fix(ci): ...`, `feat(agents): ...`)

---

## Known Active Issues

- **Flake8** violations (~687) are not CI-blocking yet — tracked in #225
- **mypy** not strict yet — tracked in #226
- **Celery/Redis** package approval pending before async task queue is fully enabled — tracked in #179
- Coverage gate is 42%; roadmap target is 70%
