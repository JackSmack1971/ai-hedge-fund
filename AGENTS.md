# Repository Guidelines

## Project Structure & Module Organization
- `src/`: core hedge-fund engine, agents, backtesting, and CLI entry points (`src/main.py`, `src/backtester.py`).
- `app/`: web application code (FastAPI backend and frontend assets).
- `tests/`: pytest suite split by domain (`tests/agents`, `tests/backend`, `tests/backtesting`, `tests/llm`, etc.).
- `docs/` and `docs2/`: project documentation and agent/process notes.
- `tools/`: utility scripts used for maintenance and development workflows.

## Build, Test, and Development Commands
- `poetry install`: install runtime and dev dependencies.
- `poetry run python src/main.py --ticker AAPL,MSFT,NVDA`: run CLI workflow.
- `poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA`: run backtests.
- `poetry run pytest`: run full test suite with coverage (`src` and `app/backend`).
- `poetry run pytest tests/backend -q`: run backend tests only.
- `poetry run black . && poetry run isort .`: format Python code.
- `poetry run flake8 . && poetry run mypy src app`: lint and type-check.

## Coding Style & Naming Conventions
- Python 3.11, 4-space indentation, max line length `120` (Black config).
- Use `snake_case` for modules/functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Keep imports sorted with `isort` (Black profile).
- Prefer small, focused modules; keep agent/business logic in `src/` and API route concerns in `app/backend`.

## Testing Guidelines
- Framework: `pytest` with `pytest-cov` and `pytest-asyncio`.
- Coverage gate is enforced via `pyproject.toml` (`--cov-fail-under=42`).
- Name tests `test_*.py` and group by feature area (for example, `tests/backend/test_routes_flows.py`).
- Add regression tests with every bug fix, especially for API routes, async flows, and backtesting logic.

## Commit & Pull Request Guidelines
- Follow Conventional Commit style seen in history (`fix(ci): ...`, `docs: ...`, `test: ...`).
- Keep commits scoped to one concern and include rationale for non-trivial behavior changes.
- PRs should include: summary, linked issue (`#123`), test evidence (commands/output), and screenshots for UI changes.
- Keep PRs small and reviewable; split large refactors from behavior changes.

## Security & Configuration Tips
- Copy `.env.example` to `.env`; never commit secrets.
- Required for web app flows: set `BACKEND_API_TOKEN` and `DATABASE_ENCRYPTION_KEY` in local env.
- Run `poetry run bandit -r src app` before merging security-sensitive changes.