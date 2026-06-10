# Repository Guidelines

## Project Structure & Module Organization
- `src/` contains the core agents, backtesting logic, and CLI entry points such as `src/main.py` and `src/backtester.py`.
- `app/` holds the FastAPI backend and web-facing code; keep route and API logic in `app/backend/`.
- `tests/` contains the pytest suite, organized by feature area like `tests/backend/`, `tests/backtesting/`, and `tests/agents/`.
- `docs/`, `docs2/`, and `tools/` store documentation, agent notes, and maintenance scripts.

## Build, Test, and Development Commands
- `poetry install` installs runtime and development dependencies.
- `poetry run python src/main.py --ticker AAPL,MSFT,NVDA` runs the main CLI workflow.
- `poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA` runs a backtest from the terminal.
- `poetry run pytest` runs the full test suite with coverage.
- `poetry run pytest tests/backend -q` runs only backend tests.
- `poetry run black . && poetry run isort .` formats code.
- `poetry run flake8 . && poetry run mypy src app` runs linting and type checks.

## Coding Style & Naming Conventions
- Use Python 3.11, 4-space indentation, and a 120-character line limit.
- Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- Keep imports sorted with `isort` using the Black profile.
- Prefer small, focused modules and keep business logic in `src/` and web concerns in `app/backend/`.

## Testing Guidelines
- The test stack is `pytest` with `pytest-cov` and `pytest-asyncio`.
- Coverage is enforced in `pyproject.toml` with a minimum of 42%.
- Name tests `test_*.py` and group them by feature area.
- Add regression tests for every bug fix, especially for API routes, async flows, and backtesting logic.

## Commit & Pull Request Guidelines
- Follow Conventional Commits, such as `fix(ci): ...`, `docs: ...`, or `test: ...`.
- Keep commits scoped to one concern and include rationale for non-trivial changes.
- Pull requests should include a short summary, linked issue number, test evidence, and screenshots for UI changes.
- Keep PRs small and reviewable; split large refactors from behavior changes.

## Security & Configuration Tips
- Copy `.env.example` to `.env` and never commit secrets.
- Web app flows require `BACKEND_API_TOKEN` and `DATABASE_ENCRYPTION_KEY`.
- Run `poetry run bandit -r src app` before merging security-sensitive changes.
