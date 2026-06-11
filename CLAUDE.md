# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

An educational AI-powered hedge fund simulation. Multiple LLM-backed agents (modeled after famous investors) analyze tickers in parallel via a LangGraph DAG, then a risk manager and portfolio manager synthesize their signals into trade decisions. It has two modes: a CLI entry point (`src/main.py`) and a full-stack web app (`app/`).

**Not for real trading.** Financial data from Financial Datasets API; free tier covers AAPL, GOOGL, MSFT, NVDA, TSLA.

---

## Commands

### Python (Poetry, Python 3.11+)

```bash
poetry install                                      # install all deps
poetry run pytest                                   # full suite (42% coverage gate)
poetry run pytest tests/backend -q                  # backend tests only
poetry run pytest tests/agents/test_all_agents.py -k "buffett" -v  # single test
poetry run pytest tests/backend/ -v --no-cov        # skip coverage (needs fake keys — see below)
poetry run black . && poetry run isort .            # format
poetry run flake8 src/ app/ tests/ --max-line-length=120
poetry run mypy src/ app/backend/ --ignore-missing-imports --no-strict-optional
poetry run bandit -r src/ app/backend/ -ll -x tests/
```

**Tests that invoke LLMs require fake API keys:**

```bash
OPENAI_API_KEY=test-key ANTHROPIC_API_KEY=test-key FINANCIAL_DATASETS_API_KEY=test-key \
  poetry run pytest tests/backend/ -v --no-cov
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

### Docker

```bash
docker-compose up hedge-fund                  # CLI default run
docker-compose up --profile embedded-ollama   # include local Ollama
docker-compose up backtester
```

---

## Architecture

### Core engine (`src/`)

The LangGraph workflow is assembled in `src/main.py::create_workflow()`. The graph shape is:

```
START → start_node → [analyst agents in parallel] → risk_management_agent → portfolio_manager → END
```

**`src/graph/state.py`** — defines `AgentState` (TypedDict flowing through the graph):

- `messages`: appended with `operator.add`
- `data` and `metadata`: merged with `merge_dicts` (last-write-wins per key)

**`src/agents/`** — one file per analyst (e.g., `warren_buffett.py`). Each agent function receives `AgentState`, calls tools to fetch financial data, invokes the LLM, and returns a partial state update with signals stored in `state["data"]["analyst_signals"]`.

**`src/utils/analysts.py`** — `ANALYST_CONFIG` is the single source of truth for all 18 analyst agents. `get_analyst_nodes()` returns `{key: (node_name, fn)}` for wiring into LangGraph. Add new analysts here.

**`src/llm/models.py`** — `get_model(name, provider)` returns a cached LangChain chat model. Models are defined in `src/llm/api_models.json` and `src/llm/ollama_models.json`. Supported providers: OpenAI, Anthropic, Groq, DeepSeek, Google, xAI, Azure OpenAI, Ollama, OpenRouter, GigaChat.

**`src/data/`** — financial data fetching via `src/tools/api.py` and an in-memory per-run cache (`src/data/cache.py`) keyed by ticker to avoid duplicate API calls.

**`src/backtesting/`** — standalone backtesting engine; `engine.py` drives date iteration, `portfolio.py` tracks positions, `metrics.py` computes Sharpe/drawdown, `trader.py` converts signals to orders.

### Web app (`app/`)

**Backend** — FastAPI in `app/backend/main.py`. Schema is owned by Alembic migrations (`app/backend/alembic/`; run `alembic upgrade head` on deploy). The lifespan handler only runs `Base.metadata.create_all()` when `AUTO_CREATE_TABLES=true` for local/dev bootstrap; production deployments should leave it disabled and rely on migrations. Key routes:

#### Backend (`app/backend/`)

FastAPI in `app/backend/main.py`. Uses `Base.metadata.create_all()` only when `AUTO_CREATE_TABLES=true`; deploy schema changes through Alembic migrations and run `alembic upgrade head` before starting the app.

Key routes (all under `app/backend/routes/`):

> > > > > > > 

| Route                            | File                        | Notes                                                    |
| -------------------------------- | --------------------------- | -------------------------------------------------------- |
| `POST /hedge-fund/run`           | `routes/hedge_fund.py`      | Streams SSE; calls same `run_hedge_fund()` logic as CLI  |
| `POST /hedge-fund/backtest`      | `routes/hedge_fund.py`      | Streams SSE for backtest progress                        |
| `POST /flows`, `GET /flows/{id}` | `routes/flows.py`           | Saved React Flow configurations (nodes+edges+viewport)   |
| `POST /flow-runs/{id}`           | `routes/flow_runs.py`       | Async execution via Celery                               |
| `POST /api-keys`                 | `routes/api_keys.py`        | Encrypted DB storage; requires `DATABASE_ENCRYPTION_KEY` |
| `GET /language-models`           | `routes/language_models.py` | Available LLM list                                       |
| `WS /ws/flow-run/{id}`           | `routes/websocket.py`       | Real-time flow-run events                                |

Repository pattern: `app/backend/repositories/` owns DB access; `app/backend/services/` holds business logic (no FastAPI imports).

**Critical: React Flow → LangGraph translation** (`app/backend/services/graph.py`):

The web app allows users to visually build agent graphs. When a run is triggered, `create_graph(graph_nodes, graph_edges)` translates the React Flow JSON into a LangGraph `StateGraph`. Node IDs in the web app have a 6-character alphanumeric suffix (e.g., `warren_buffett_abc123`); `extract_base_agent_key()` strips this suffix to look up the agent in `ANALYST_CONFIG`. This same suffix scheme is mirrored in the frontend (`app/frontend/src/data/node-mappings.ts`).

#### Frontend (`app/frontend/`)

React 18 + Vite 5 + TypeScript + TailwindCSS **3** (not 4). Uses `@xyflow/react` v12 for the agent graph visualization, shadcn/ui + Radix primitives. Source in `app/frontend/src/`.

Key frontend patterns:

- `src/contexts/flow-context.tsx` — manages save/load of React Flow state; wraps ReactFlow API
- `src/contexts/node-context.tsx` — per-node model selection and agent data (status, signals)
- `src/contexts/tabs-context.tsx` — tab management for the IDE-like layout
- `src/nodes/` — custom node components for `agent-node`, `portfolio-manager-node`, `portfolio-start-node`, `stock-analyzer-node`, output nodes
- `src/data/node-mappings.ts` — maps sidebar component names → node creation functions (calls backend to get agent list)
- `src/services/flow-service.ts` — HTTP client for backend flow CRUD

#### Async tasks

Celery + Redis (`REDIS_URL` env var). Worker defined in `app/backend/tasks/`. **Package approval pending** — tracked in issue #179.

### Test layout

```
tests/
├── agents/       # agent logic, regression tests per investor
├── backend/      # FastAPI routes and services (httpx AsyncClient + mocks)
├── backtesting/  # integration tests with mocked financial data
├── llm/          # model selection/provider logic
├── data/         # caching and data-fetch mocks
└── cli/          # CLI argument parsing
```

Coverage measured over `src/` and `app/backend/` (not frontend). Gate is 42%.

---

## Environment Variables

Copy `.env.example` to `.env`.

| Variable                     | Purpose                                                   |
| ---------------------------- | --------------------------------------------------------- |
| `OPENAI_API_KEY`             | Primary LLM provider                                      |
| `ANTHROPIC_API_KEY`          | Claude models                                             |
| `GROQ_API_KEY`               | Fast inference                                            |
| `FINANCIAL_DATASETS_API_KEY` | Market data                                               |
| `BACKEND_API_TOKEN`          | Protects backend routes                                   |
| `DATABASE_ENCRYPTION_KEY`    | Encrypts stored API keys                                  |
| `REDIS_URL`                  | Celery broker (default `redis://localhost:6379/0`)        |
| `CORS_ORIGINS`               | Comma-separated allowed origins (default: localhost:5173) |

---

## Code Style

- **Line length**: 120 (Black + flake8)
- **Formatting**: Black + isort (`profile = "black"`)
- **Mypy**: non-strict (`strict = false`, `ignore_missing_imports = true`)
- **Flake8**: ~687 violations still pending cleanup; CI runs with `continue-on-error: true` on the lint step
- **Commits**: Conventional Commits style (`fix(ci): ...`, `feat(agents): ...`)

---

## Known Active Issues

- Flake8 violations (~687) are not CI-blocking — tracked in #225
- mypy not strict yet — tracked in #226
- Celery/Redis package approval pending — tracked in #179
- Coverage gate is 42%; roadmap target is 70%
