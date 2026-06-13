# Repository Guidelines

## Intent Layer
This repository uses `AGENTS.md` as the canonical root context file. Do not add a second root context file.

Read this file first, then the nearest child node:
- [src/AGENTS.md](./src/AGENTS.md) for the core engine, agents, data, and backtesting code.
- [app/backend/AGENTS.md](./app/backend/AGENTS.md) for FastAPI routes, services, repositories, and persistence.
- [app/frontend/AGENTS.md](./app/frontend/AGENTS.md) for the React + Vite UI.
- [tests/AGENTS.md](./tests/AGENTS.md) for test layout, fixtures, and suite-specific conventions.

## Project Overview
This is an educational AI-powered hedge fund simulation. Multiple LLM-backed agents analyze tickers in parallel, then risk and portfolio management nodes synthesize signals into trade decisions.

Primary entry points:
- `src/main.py` for the CLI workflow.
- `src/backtester.py` for backtests.
- `app/backend/main.py` for the FastAPI backend.
- `app/frontend/` for the web UI.

## Repository Layout
- `src/` contains the core hedge-fund engine, agent logic, backtesting code, and CLI entry points.
- `app/backend/` holds the FastAPI backend and server-side business logic.
- `app/frontend/` contains the web UI and Node-based tooling.
- `tests/` contains the pytest suite organized by feature area.
- `docs/`, `docs2/`, and `tools/` store project documentation and maintenance scripts.

## Common Commands
- `poetry install` installs runtime and development dependencies.
- `poetry run python src/main.py --ticker AAPL,MSFT,NVDA` runs the main agent workflow.
- `poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA` runs the backtesting CLI.
- `poetry run pytest` runs the full test suite with coverage.
- `poetry run pytest tests/backend -q` runs backend tests only.
- `poetry run black . && poetry run isort .` formats Python code.
- `poetry run flake8 . && poetry run mypy src app` runs linting and type checks.

## Coding Standards
- Use Python 3.11, 4-space indentation, and a 120-character line limit.
- Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- Keep imports sorted with `isort` using the Black profile.
- Prefer small, focused modules and keep business logic in `src/` and web concerns in `app/backend/`.

## Testing Standards
- The project uses `pytest`, `pytest-cov`, and `pytest-asyncio`.
- Coverage is enforced in `pyproject.toml` with a minimum of 42%.
- Name tests `test_*.py` and group them by feature area.
- Add regression tests for every bug fix, especially for API routes, async flows, and backtesting logic.

## Delivery Standards
- Use Conventional Commits, such as `fix(ci): ...`, `docs: ...`, or `test: ...`.
- Keep commits scoped to one concern and include rationale for non-trivial changes.
- Pull requests should include a short summary, linked issue number, test evidence, and screenshots for UI changes.
- Keep PRs small and reviewable; split large refactors from behavior changes.

## Security & Configuration
- Copy `.env.example` to `.env` and never commit secrets.
- Web app flows require `BACKEND_API_TOKEN` and `DATABASE_ENCRYPTION_KEY`.
- Run `poetry run bandit -r src app` before merging security-sensitive changes.
