# Testing Patterns

**Analysis Date:** 2026-06-09

## Test Framework

**Runner & Assertion:**
- Pytest (configured via `pyproject.toml`).
- Uses standard Python `assert` statements.
- Async test runner: `pytest-asyncio` (strict mode enabled by default).

**Run Commands:**
```bash
poetry run pytest                                   # Run the full test suite (with coverage)
poetry run pytest tests/backend -q                  # Run only backend routes and services tests
poetry run pytest tests/agents/test_all_agents.py   # Run only agent correctness tests
poetry run pytest tests/backend/ -v --no-cov        # Run backend tests skipping coverage
poetry run pytest tests/agents/test_all_agents.py -k "buffett" -v  # Run specific agent test
```

## Test File Organization

**Location:**
- Dedicated `tests/` root directory mirroring the `src/` and `app/backend/` layouts.
- Test files are not collocated with source code.

**Structure:**
```
tests/
├── agents/             # Tests validating each of the 18 analyst agents
│   └── test_all_agents.py
├── backend/            # FastAPI integration tests (database, repositories, routes)
│   ├── conftest.py
│   ├── test_db_connection.py
│   ├── test_routes_db_session.py
│   └── test_routes_flows.py
├── backtesting/        # Offline backtester module tests (portfolio, metrics, engine)
│   ├── conftest.py
│   └── test_portfolio.py
├── cli/                # Tests for command line inputs
├── data/               # Tests validating the pricing caches
└── llm/                # Tests verifying LLM model selection logic
```

## Test Suite Structure

**Suite Organization:**
- Tests are grouped in classes or as flat functions.
- Every test function must start with `test_` (e.g., `test_run_endpoint_closes_db_session`).
- Uses `unittest.mock.patch` context managers or decorators to isolate external integrations.

**Example Route Test:**
```python
class TestDbSessionReleasedBeforeStreaming:
    def test_run_endpoint_closes_db_session(self):
        from app.backend.models.schemas import HedgeFundRequest
        from app.backend.routes.hedge_fund import run

        db = MagicMock()
        with (
            patch("app.backend.routes.hedge_fund.create_portfolio"),
            patch("app.backend.routes.hedge_fund.create_graph"),
        ):
            request_data = HedgeFundRequest(
                tickers=["AAPL"],
                graph_nodes=[{"id": "n1", "type": "analyst"}],
                graph_edges=[],
                start_date="2024-01-01",
                end_date="2024-03-31",
                model_name="gpt-4o",
                model_provider="OpenAI",
            )
            asyncio.run(run(request_data, MagicMock(), db))

        db.close.assert_called_once()
```

## Mocking

**Framework:**
- Standard library `unittest.mock` (`MagicMock`, `AsyncMock`, `patch`).

**Mocking Patterns:**
- **External API Keys:** Fake credentials are set as environment variables or provided in the request payload to satisfy configuration checks (e.g., `OPENAI_API_KEY="test-key"`).
- **HTTP Endpoints:** `requests` responses are mocked or patched to return static pricing structure.
- **LLM Invocations:** LangChain chat clients are mocked during agent execution tests to prevent real network calls.

## Fixtures and Factories

**Shared Fixtures (`tests/backend/conftest.py`):**
- `db_session`: Bootstraps an in-memory SQLite database (`sqlite:///:memory:`), creates all tables from SQLAlchemy `Base`, yields the session, and drops tables on teardown. Ensure tests are isolated and hermetic.
- `test_app`: Provides a FastAPI `TestClient` with app startup database initialization mocked to run tests without running Ollama network checks.

**Backtesting Fixtures (`tests/backtesting/conftest.py`):**
- `portfolio`: Generates a standard mock portfolio with tickers AAPL and MSFT, cash, and margin configuration.
- `prices`: Returns a static dictionary mapping tickers to mock stock prices.
- `price_df_factory`: Returns a helper function generating minimal pandas DataFrames containing price lists.

## Coverage

**Requirements:**
- Minimum coverage requirement: **42%** (enforced in `pyproject.toml` via `--cov-fail-under=42`).
- CI pipeline will fail if coverage drops below this gate.
- Exclusions: `tests/` directory and CLI visualization module `src/utils/display.py` are omitted from coverage calculations.

---

*Testing analysis: 2026-06-09*
*Update when test patterns change*
