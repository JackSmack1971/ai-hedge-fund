# Codebase Concerns

**Analysis Date:** 2026-06-09

## Tech Debt

**Dual Database Table Initialization:**
- Issue: Backend uses both direct `Base.metadata.create_all(bind=engine)` at startup and Alembic migrations.
- Files: `app/backend/main.py` (line ~20), `app/backend/alembic/`
- Impact: Auto-creation of tables at runtime can mask out-of-sync migrations and create deployment-time schema drift conflicts.
- Fix approach: Rely entirely on Alembic for production and local migrations; remove `create_all` from runtime startup.

**Unresolved Linting Violations (Flake8):**
- Issue: ~687 unresolved flake8 violations are present, forcing CI to run with `continue-on-error: true` for the linting step.
- File: `.github/workflows/test.yml` (line ~47)
- Impact: New style/formatting bugs can be committed without failing the build pipeline.
- Fix approach: Incrementally fix the flake8 warnings, resolve issue #225, and remove `continue-on-error: true` from the lint step.

**Non-Strict Type Checking (Mypy):**
- Issue: Mypy is configured in non-strict mode (`strict = false`), and missing stub packages force the CI step to run with `continue-on-error: true`.
- Files: `pyproject.toml` (line ~82), `.github/workflows/test.yml` (line ~56)
- Impact: Type errors go unnoticed in the CI pipeline.
- Fix approach: Add missing type stubs, clean up type errors in backend files, and enforce a non-permissive Mypy check in CI.

## Security Considerations

**Database Encryption Key Management:**
- Risk: API keys stored in the database are encrypted using Fernet; if `DATABASE_ENCRYPTION_KEY` is misconfigured or lost, all saved API keys become unrecoverable and decrypt calls will throw crashes.
- File: `app/backend/routes/api_keys.py`
- Current mitigation: Checked on startup; relies on proper environment variable ingestion.
- Recommendations: Implement a health check validating key usability without dumping actual secrets.

**Test Directory Bandit Exclusions:**
- Risk: Bandit is configured to completely bypass the `tests/` directory.
- File: `pyproject.toml` (line ~89), `.github/workflows/test.yml` (line ~63)
- Current mitigation: Standard security gate runs only on `src/` and `app/backend/`.
- Recommendations: Ensure no production tokens or hardcoded secrets are accidentally added to test fixtures or files.

## Performance Bottlenecks

**Bulk Prefetch Memory Allocation:**
- Problem: `BacktestService.prefetch_data` queries all prices, metrics, insider trades, and news for the entire period up-front.
- File: `app/backend/services/backtest_service.py` (line ~224)
- Impact: A year-long backtest with several tickers can allocate massive pandas DataFrames/arrays, resulting in memory spikes.
- Improvement path: Implement chunked/paginated caching or fetch-on-demand for backtesting instead of massive prefetching.

**SQLite Concurrency Limits:**
- Problem: High concurrent flow execution writes multiple run logs and states to the single SQLite file.
- Impact: SQLite's write locking can lead to `database is locked` or timeout exceptions if multiple backtests execute concurrently.
- Improvement path: Leverage the WAL mode connect pragmas currently in place, but consider migrating to PostgreSQL for production environments.

## Fragile Areas

**Suffix-Based Node ID Mapping:**
- Why fragile: Visual graphs use custom React Flow IDs containing a 6-character alphanumeric suffix (e.g. `warren_buffett_abc123`). The backend parses these using `extract_base_agent_key()` by stripping the suffix.
- Files: `app/backend/services/graph.py`, `app/frontend/src/data/node-mappings.ts`
- Common failures: If the frontend changes its suffix format (e.g., changes length or character set), the backend will fail to map the nodes to their corresponding base agent in `ANALYST_CONFIG`.
- Safe modification: Add a explicit `agent_key` or `type` property in the React Flow node data payload rather than parsing string suffixes.
- Test coverage: Partially covered by `tests/backend/test_routes_flows.py`, but missing exhaustive edge-case test validations.

## Scaling Limits

**Financial Datasets API Free Tier:**
- Limit: The free API tier is restricted to AAPL, GOOGL, MSFT, NVDA, and TSLA.
- Symptoms: Queries for any other stock ticker return empty responses or error codes.
- Scaling path: User must supply their own paid API key in settings or env.

**Celery/Redis Package Approval Dependency:**
- Issue: Production asynchronous execution via Celery workers is currently blocked pending package license/review approval.
- File: `app/backend/tasks/`
- Impact: The app cannot run background tasks in production pipelines without Celery approved; currently runs in-process or synchronously.

## Test Coverage Gaps

**Low Global Coverage Target (42%):**
- What's not tested: Visual React Flow graph translators, Celery async tasks, and UI React rendering components have minimal or zero test coverage.
- Risk: Code refactors inside the frontend or task runners can cause silent failures that bypass the CI gate.
- Priority: Medium.
- Difficulty to test: Testing complex visual graphs requires UI test libraries (like Playwright) and mocked websocket servers.

---

*Concerns audit: 2026-06-09*
*Update as issues are fixed or new ones discovered*
