# Codebase Structure

**Analysis Date:** 2026-06-09

## Directory Layout

```
ai-hedge-fund/
├── .github/                  # GitHub specific configuration
│   └── workflows/            # CI pipeline workflow files
├── app/                      # Web Application
│   ├── backend/              # FastAPI application root
│   │   ├── alembic/          # Alembic database migration scripts
│   │   ├── database/         # Database connection pool and SQLite setup
│   │   ├── models/           # FastAPI Pydantic requests & SSE event schemas
│   │   ├── repositories/     # Repository layer isolating DB queries
│   │   ├── routes/           # REST endpoints, WebSocket and SSE routers
│   │   ├── security/         # Encryption and authorization utilities
│   │   ├── services/         # Core web services (graph compiler, backtest service)
│   │   ├── tasks/            # Async task definitions (Celery/Redis worker)
│   │   └── utils/            # Backend helper functions
│   └── frontend/             # React SPA (Vite + TS + TailwindCSS 3)
│       ├── public/           # Static public assets
│       └── src/              # React sources (components, contexts, nodes, services)
├── docker/                   # Docker deployment configurations
├── docs/                     # Project documentation files
├── outputs/                  # Exported run data and plots
├── src/                      # Core Multi-Agent Hedge Fund Logic (CLI Engine)
│   ├── agents/               # Investment analyst agent definitions
│   ├── backtesting/          # Offline backtesting simulation engine
│   ├── cli/                  # CLI input argument parsing
│   ├── data/                 # Data caching and Pydantic models
│   ├── graph/                # LangGraph state configuration
│   ├── llm/                  # LLM models setup (cached client creators)
│   ├── tools/                # API client fetching financial market data
│   └── utils/                # CLI console display and progress tracking helpers
├── tests/                    # Testing Suites
│   ├── agents/               # Tests validating analyst decisions and outputs
│   ├── backend/              # Integration tests for FastAPI endpoints and services
│   ├── backtesting/          # Tests verifying metrics, portfolio, and engine
│   ├── cli/                  # Tests validating CLI arguments and inputs
│   ├── data/                 # Tests for the in-memory pricing cache
│   ├── fixtures/             # JSON/mock data files for testing
│   ├── llm/                  # Tests verifying model configs and providers
│   └── tools/                # Tests verifying API client integrations
└── tools/                    # Repository scripts and tools
```

## Directory Purposes

**app/backend/**
- Purpose: FastAPI web backend.
- Contains: `*.py` service files, Alembic configs, and database repositories.
- Key files: `app/backend/main.py` (API entry point), `app/backend/routes/hedge_fund.py` (SSE runner), `app/backend/services/graph.py` (LangGraph compiler).
- Subdirectories: `routes/`, `services/`, `models/`, `repositories/`, `database/`, `tasks/`.

**app/frontend/src/**
- Purpose: React client application.
- Contains: `*.ts`, `*.tsx`, `*.css` components.
- Key files: `src/contexts/flow-context.tsx` (state graph manager), `src/nodes/agent-node.tsx` (custom React Flow node).
- Subdirectories: `contexts/`, `nodes/`, `services/`, `components/`, `data/`.

**src/**
- Purpose: Core CLI hedge fund engine.
- Contains: `*.py` agent workflows and utilities.
- Key files: `src/main.py` (CLI entry), `src/backtester.py` (offline backtesting CLI), `src/tools/api.py` (Financial Datasets client).
- Subdirectories: `agents/`, `backtesting/`, `data/`, `graph/`, `llm/`, `tools/`, `utils/`.

**tests/**
- Purpose: Pytest unit and integration test suite.
- Contains: `test_*.py` test files and `conftest.py` setups.
- Key files: `tests/backend/conftest.py` (hermetic DB/client fixtures), `tests/agents/test_all_agents.py` (agent verification).

## Key File Locations

**Entry Points:**
- `src/main.py` - CLI trading runner.
- `src/backtester.py` - CLI backtesting runner.
- `app/backend/main.py` - FastAPI backend server.
- `app/frontend/src/main.tsx` - Frontend application entry.

**Configuration:**
- `pyproject.toml` - Python dependencies (Poetry), black/isort/pytest/mypy configurations.
- `app/frontend/package.json` - Frontend Node dependencies and scripts.
- `app/frontend/tailwind.config.ts` - TailwindCSS style utility configs.
- `app/backend/alembic.ini` - Alembic migration DB path config.

**Core Logic:**
- `src/utils/analysts.py` - Analysts registry (`ANALYST_CONFIG`).
- `src/llm/models.py` - Chat model instance creator and manager.
- `app/backend/services/graph.py` - Layout translator converting UI graph schema to executable DAG.

## Naming Conventions

**Files:**
- `snake_case.py` - All Python modules.
- `kebab-case.ts/tsx` - Frontend TypeScript sources, components, and contexts.
- `test_*.py` - Test files (always matching source name).

**Directories:**
- `snake_case` - All Python directories.
- `kebab-case` - Frontend directories.

## Where to Add New Code

**New Analyst/Investor Agent:**
1. Create new agent module in `src/agents/` (e.g. `src/agents/my_agent.py`), implementing an agent function.
2. Register the agent in `ANALYST_CONFIG` inside `src/utils/analysts.py`.
3. Add a unit test in `tests/agents/` (or update `tests/agents/test_all_agents.py`).
4. Update frontend mapping file `app/frontend/src/data/node-mappings.ts` if specific visual mappings or forms are needed.

**New API Endpoint:**
1. Define the route handler in the relevant router in `app/backend/routes/` (e.g. `routes/hedge_fund.py`).
2. Add necessary request/response Pydantic models in `app/backend/models/schemas.py`.
3. Write integration tests in `tests/backend/test_routes_*.py`.

**New Backend Database Model:**
1. Define the SQLAlchemy model in `app/backend/database/models.py`.
2. Generate an Alembic migration script using `poetry run alembic revision --autogenerate -m "description"`.
3. Create corresponding Pydantic schema in `app/backend/models/schemas.py`.
4. Create repository functions in `app/backend/repositories/`.

---

*Structure analysis: 2026-06-09*
*Update when directory structure changes*
```
