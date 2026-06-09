# Coding Conventions

**Analysis Date:** 2026-06-09

## Naming Patterns

### Python Backend & Engine

**Files & Modules:**
- `snake_case.py` (e.g., `michael_burry.py`, `portfolio_manager.py`).
- Test files must be prefixed with `test_` followed by the exact file name (e.g., `test_routes_db_session.py`).

**Classes:**
- `PascalCase` (e.g., `BacktestEngine`, `PerformanceMetrics`, `ApiKeyService`).
- Pydantic request models: `*Request` (e.g., `HedgeFundRequest`, `BacktestRequest`).
- Pydantic response models: `*Response` (e.g., `ErrorResponse`).

**Functions & Methods:**
- `snake_case` (e.g., `run_hedge_fund()`, `create_workflow()`, `execute_trade()`).
- No special prefix for asynchronous functions (`async def run()`).

**Variables:**
- `snake_case` (e.g., `selected_analysts`, `portfolio_positions`, `current_prices`).
- Private variables/methods inside modules must use a single leading underscore prefix `_` (e.g., `_build_model()`, `_default_origins`, `_is_sqlite`).

**Constants:**
- `UPPER_SNAKE_CASE` (e.g., `AVAILABLE_MODELS`, `ANALYST_CONFIG`, `DATABASE_URL`).

### Frontend (TypeScript / React)

**Files & Directories:**
- `kebab-case.ts` / `kebab-case.tsx` (e.g., `flow-context.tsx`, `agent-node.tsx`).
- Plural names for folders containing collections (e.g., `contexts/`, `nodes/`, `components/`).

**Variables & Functions:**
- `camelCase` (e.g., `flowContext`, `nodeData`, `getAgents()`).
- Custom hook prefix: `use` (e.g., `useFlow()`).

**Interfaces & Types:**
- `PascalCase` (e.g., `NodeData`, `FlowService`). No `I` prefix.

## Code Style

**Formatting (Python):**
- Indentation: 4 spaces.
- Maximum line length: 120 characters (enforced by Black and Flake8).
- String quotes: Double quotes `"` preferred.
- Automatic formatting via Black (`poetry run black .`).

**Linting & Verification (Python):**
- Lint checks: Flake8 (`poetry run flake8 src/ app/ tests/ --max-line-length=120`).
- Type checks: Mypy (`poetry run mypy src/ app/backend/ --ignore-missing-imports --no-strict-optional`). Strict mode is disabled.
- Security scan: Bandit (`poetry run bandit -r src/ app/backend/ -ll -x tests/`).

**Formatting & Linting (Frontend):**
- Indentation: 2 spaces.
- ESLint checked (`npm run lint`).
- Styled using TailwindCSS 3.4.

## Import Organization

**Python Import Order (enforced by isort):**
1. Standard library imports (e.g., `import json`, `import os`).
2. Third-party library imports (e.g., `from fastapi import FastAPI`, `from sqlalchemy.orm import Session`).
3. Local/application imports (e.g., `from src.agents import ...`, `from app.backend.database import ...`).

**Grouping:**
- Blank line separating each import group.
- Imports must be sorted alphabetically within each group.
- Configured via `poetry run isort .` (utilizing the `black` profile).

## Error Handling

**Strategy:**
- Throw descriptive exceptions inside core engine logic or services and catch them at route controllers or CLI entry points.
- Route handlers capture exceptions, log detailed errors, and yield an `ErrorEvent` (in SSE streams) or raise `HTTPException` with appropriate status code.
- Input validation is handled at the network boundary using Pydantic validation schemas.
- Clean up resources gracefully (e.g., `db.close()` inside a `finally` block or context manager).

## Logging

**Framework:**
- Standard Python `logging` module configured in `app/backend/main.py`.
- Module-level loggers defined via `logger = logging.getLogger(__name__)`.
- Logging level set to `INFO` (development logs detail Ollama readiness, server endpoints, and execution states).

## Comments

- **Tone & Content:** Focus on explaining *why* a particular workaround or tuning parameter was implemented rather than *what* the code is doing.
- **Docstrings:** Use docstrings for all public modules, classes, and functions. Follow triple-quotes `"""` standard describing arguments, returns, and exceptions.
- **Git Commits:** Follow Conventional Commits format (e.g., `feat(agents): add stanley druckenmiller`, `fix(ci): pin action versions`).

---

*Convention analysis: 2026-06-09*
*Update when patterns change*
