<!-- GSD:project-start source:PROJECT.md -->

## Project

**AI Hedge Fund — Hybrid Decision Engine**

An educational proof of concept for an AI-powered hedge fund and backtesting system. It compiles visual agent DAGs into LangGraph workflows, allowing LLM-based analyst agents to generate trading signals that are processed through risk management and portfolio management layers.

**Core Value:** LLMs may reason, critique, debate, and analyze, but deterministic mathematical and risk controls must retain final authority over trading actions, position sizing, admissibility, and backtest accounting.

### Constraints

- **Tech Stack**: Must use Python 3.11, Poetry, LangGraph, LangChain, and SQLite.
- **Security**: Database encryption key management via Fernet must be robustly handled.
- **Compatibility**: The system must run in baseline mode unless hybrid features are explicitly enabled via flags.
- **Licensing**: Celery worker integration is blocked pending package license approval.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.11 - Backend service, agent logic, backtesting engine, and CLI entry points.
- TypeScript 5.3 - Frontend React application code.
- JavaScript - Build scripts, linting/formatting configs (Vite, Tailwind, ESLint, PostCSS).

## Runtime

- Python 3.11+ - Executed locally or via Docker containers.
- Node.js 20.x (LTS) - For compiling and running the Vite/React frontend.
- Poetry 1.7.1 - Backend package management. Lockfile: `poetry.lock` present.
- npm 10.x - Frontend package management. Lockfile: `package-lock.json` present.

## Frameworks

- FastAPI 0.104.0 - Backend REST API server and SSE streaming.
- LangGraph 0.3.0 - Orchestrates the multi-agent DAG workflow.
- LangChain 0.3.7 - Core LLM abstraction layer and provider integrations.
- React 18.2 - Frontend user interface.
- Vite 5.0.12 - Frontend build tool and development server.
- Pytest 8.3 - Python test runner.
- Pytest-Cov - Coverage reporting.
- Pytest-Asyncio - Async test support.
- ESLint 8.56.0 - Frontend linting tool.
- Black 24.0 - Python code formatting.
- Isort 5.12.0 - Python import sorting.
- Flake8 6.1.0 - Python code linting.
- Mypy 1.10 - Python static type checking.
- Bandit 1.7 - Python security scanning.
- Uvicorn 0.22.0+ - ASGI server running FastAPI.

## Key Dependencies

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
- `pandas` 2.1.0 - Data frames for financial data manipulation.
- `numpy` >=2.0,<3 - Numerical computation.
- `requests` - HTTP client for financial APIs.
- `httpx` 0.27.0 - Async HTTP client for backend and tests.
- `redis` 5.0.0+ - Celery message broker.
- `shadcn-ui` 0.9.5 - Accessible frontend components styled with Tailwind.

## Configuration

- `.env` / `.env.example` - Backend and API secrets (e.g. `OPENAI_API_KEY`, `FINANCIAL_DATASETS_API_KEY`).
- Configured via `python-dotenv` at runtime.
- `pyproject.toml` - Full Poetry setup, Pytest options, Black line limit (120), Mypy settings.
- `app/frontend/vite.config.ts` - Vite configuration for dev server proxy and react plugin.
- `app/frontend/tailwind.config.ts` - TailwindCSS 3.4 configuration.

## Platform Requirements

- Windows/macOS/Linux with Python 3.11+ and Node.js 20+.
- Financial Datasets API key for stock price queries.
- Docker / Docker Compose - Multi-container setup (FastAPI, Redis, Celery worker, Ollama).
- SQLite db (`app/backend/hedge_fund.db`) or cloud PostgreSQL target via `DATABASE_URL`.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

### Python Backend & Engine

- `snake_case.py` (e.g., `michael_burry.py`, `portfolio_manager.py`).
- Test files must be prefixed with `test_` followed by the exact file name (e.g., `test_routes_db_session.py`).
- `PascalCase` (e.g., `BacktestEngine`, `PerformanceMetrics`, `ApiKeyService`).
- Pydantic request models: `*Request` (e.g., `HedgeFundRequest`, `BacktestRequest`).
- Pydantic response models: `*Response` (e.g., `ErrorResponse`).
- `snake_case` (e.g., `run_hedge_fund()`, `create_workflow()`, `execute_trade()`).
- No special prefix for asynchronous functions (`async def run()`).
- `snake_case` (e.g., `selected_analysts`, `portfolio_positions`, `current_prices`).
- Private variables/methods inside modules must use a single leading underscore prefix `_` (e.g., `_build_model()`, `_default_origins`, `_is_sqlite`).
- `UPPER_SNAKE_CASE` (e.g., `AVAILABLE_MODELS`, `ANALYST_CONFIG`, `DATABASE_URL`).

### Frontend (TypeScript / React)

- `kebab-case.ts` / `kebab-case.tsx` (e.g., `flow-context.tsx`, `agent-node.tsx`).
- Plural names for folders containing collections (e.g., `contexts/`, `nodes/`, `components/`).
- `camelCase` (e.g., `flowContext`, `nodeData`, `getAgents()`).
- Custom hook prefix: `use` (e.g., `useFlow()`).
- `PascalCase` (e.g., `NodeData`, `FlowService`). No `I` prefix.

## Code Style

- Indentation: 4 spaces.
- Maximum line length: 120 characters (enforced by Black and Flake8).
- String quotes: Double quotes `"` preferred.
- Automatic formatting via Black (`poetry run black .`).
- Lint checks: Flake8 (`poetry run flake8 src/ app/ tests/ --max-line-length=120`).
- Type checks: Mypy (`poetry run mypy src/ app/backend/ --ignore-missing-imports --no-strict-optional`). Strict mode is disabled.
- Security scan: Bandit (`poetry run bandit -r src/ app/backend/ -ll -x tests/`).
- Indentation: 2 spaces.
- ESLint checked (`npm run lint`).
- Styled using TailwindCSS 3.4.

## Import Organization

- Blank line separating each import group.
- Imports must be sorted alphabetically within each group.
- Configured via `poetry run isort .` (utilizing the `black` profile).

## Error Handling

- Throw descriptive exceptions inside core engine logic or services and catch them at route controllers or CLI entry points.
- Route handlers capture exceptions, log detailed errors, and yield an `ErrorEvent` (in SSE streams) or raise `HTTPException` with appropriate status code.
- Input validation is handled at the network boundary using Pydantic validation schemas.
- Clean up resources gracefully (e.g., `db.close()` inside a `finally` block or context manager).

## Logging

- Standard Python `logging` module configured in `app/backend/main.py`.
- Module-level loggers defined via `logger = logging.getLogger(__name__)`.
- Logging level set to `INFO` (development logs detail Ollama readiness, server endpoints, and execution states).

## Comments

- **Tone & Content:** Focus on explaining *why* a particular workaround or tuning parameter was implemented rather than *what* the code is doing.
- **Docstrings:** Use docstrings for all public modules, classes, and functions. Follow triple-quotes `"""` standard describing arguments, returns, and exceptions.
- **Git Commits:** Follow Conventional Commits format (e.g., `feat(agents): add stanley druckenmiller`, `fix(ci): pin action versions`).

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## Pattern Overview

- **Dynamic DAG Compilation:** Translates visual graphs built with React Flow in the frontend into runnable LangGraph state machines in the backend.
- **Parallel Analysis:** Runs multiple LLM-backed analyst agents simultaneously to generate specialized trading signals.
- **Sequential Synthesis:** Forwards signals sequentially through a Risk Manager and a Portfolio Manager to make final trading actions.
- **Streaming Execution:** Emits real-time progress updates and intermediate decisions via Server-Sent Events (SSE).

## Layers

- Purpose: Interactive workspace for designing agent networks, configuring models, and visualizing real-time run/backtest updates.
- Location: `app/frontend/src/`
- Key Abstractions: `flow-context.tsx`, `node-context.tsx`, `tabs-context.tsx`.
- Depends on: Backend API endpoints.
- Purpose: Exposes HTTP routes, handles serialization/validation, and streams execution events.
- Location: `app/backend/routes/`
- Depends on: Services and repositories.
- Purpose: Core application services (flow creation, dynamic graph assembly, encrypted key management, backtesting logic).
- Location: `app/backend/services/`
- Key Files:
- Depends on: Repositories and CLI engine modules.
- Purpose: Encapsulates database reads and writes.
- Location: `app/backend/repositories/`
- Depends on: SQLAlchemy models and connection engines.
- Purpose: Autonomous trading execution pipeline (CLI endpoints and Agent execution).
- Location: `src/`
- Key Files:

## Data Flow

### SSE-Streamed Visual Run Flow (Web App)

### Historical CLI Backtest Flow

## Key Abstractions

- Purpose: TypedDict representing state flowing between graph nodes.
- Keys:
- Purpose: Single source of truth defining the available 18 analyst agents, their descriptions, styles, and backing agent functions.
- Purpose: LRU-cached factory function (`get_model`) returning a LangChain chat client instance mapped to the provider type. Prevents duplicate client instantiation.

## Error Handling

- **API Rate Limits:** `src/tools/api.py` traps HTTP 429 errors and retries requests using a full-jitter exponential backoff, complying with `Retry-After` headers if present.
- **DB Connection Leaks:** Web API endpoints call `db.close()` immediately after resolving keys, preventing active SQLite connections from remaining blocked during long-running streams.
- **Client Disconnection:** SSE endpoint runs a concurrent `wait_for_disconnect` task; if the HTTP connection drops, the async graph task is cancelled immediately.

## Cross-Cutting Concerns

- **Symmetric Encryption:** API keys are encrypted at-rest using `Fernet` (AES-128 in CBC mode) with key `DATABASE_ENCRYPTION_KEY` before database insertion.
- **Task Delegation:** Long-running flow runs can be offloaded asynchronously to Celery workers using Redis as the message broker.

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.agent/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
