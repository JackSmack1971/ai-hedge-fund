# Architecture

**Analysis Date:** 2026-06-09

## Pattern Overview

**Overall:** Multi-Agent Trading System with Dynamic Visual Orchestration.

**Key Characteristics:**
- **Dynamic DAG Compilation:** Translates visual graphs built with React Flow in the frontend into runnable LangGraph state machines in the backend.
- **Parallel Analysis:** Runs multiple LLM-backed analyst agents simultaneously to generate specialized trading signals.
- **Sequential Synthesis:** Forwards signals sequentially through a Risk Manager and a Portfolio Manager to make final trading actions.
- **Streaming Execution:** Emits real-time progress updates and intermediate decisions via Server-Sent Events (SSE).

## Layers

**User Interface (Frontend):**
- Purpose: Interactive workspace for designing agent networks, configuring models, and visualizing real-time run/backtest updates.
- Location: `app/frontend/src/`
- Key Abstractions: `flow-context.tsx`, `node-context.tsx`, `tabs-context.tsx`.
- Depends on: Backend API endpoints.

**API Route Controller (Backend):**
- Purpose: Exposes HTTP routes, handles serialization/validation, and streams execution events.
- Location: `app/backend/routes/`
- Depends on: Services and repositories.

**Services & Business Logic:**
- Purpose: Core application services (flow creation, dynamic graph assembly, encrypted key management, backtesting logic).
- Location: `app/backend/services/`
- Key Files:
  - `app/backend/services/graph.py` - Translates React Flow layout JSON to LangGraph compiled workflows.
  - `app/backend/services/backtest_service.py` - Historical loop driver for web backtests.
- Depends on: Repositories and CLI engine modules.

**Data Access & Repositories:**
- Purpose: Encapsulates database reads and writes.
- Location: `app/backend/repositories/`
- Depends on: SQLAlchemy models and connection engines.

**Core Engine (`src/`):**
- Purpose: Autonomous trading execution pipeline (CLI endpoints and Agent execution).
- Location: `src/`
- Key Files:
  - `src/main.py` - CLI entry point and central LangGraph assembler (`create_workflow`).
  - `src/backtester.py` - CLI entry point for local backtests.

## Data Flow

### SSE-Streamed Visual Run Flow (Web App)

1. Client posts React Flow JSON to `/hedge-fund/run` endpoint.
2. Router resolves API credentials from DB, closes DB connection early to prevent connection pool exhaustion during streaming, and initializes the portfolio state.
3. Services compile the custom LangGraph from client nodes and edges. Suffixes from visual nodes (e.g. `_abc123`) are extracted to resolve base agent configurations in `src/utils/analysts.py`.
4. Router starts `run_graph_async` background task and begins an SSE streaming generator.
5. The generator registers a progress callback with `src/utils/progress.py::progress`.
6. As LangGraph executes:
   - `start_node` runs.
   - Selected analyst nodes run in parallel. Each analyst fetches historical financials/news from the cache/API, invokes the cached LLM client, and appends signals to `AgentState`.
   - `risk_management_agent` processes signals and determines risk thresholds.
   - `portfolio_manager` consumes final recommendations, outputs final JSON decisions, and terminates.
7. The SSE generator captures progress events, yields SSE packets (`Start`, `Progress`, `Complete`, `Error`), and handles connection disconnects by cancelling the background task.

### Historical CLI Backtest Flow

1. User executes `poetry run python src/backtester.py --ticker AAPL --start-date 2024-01-01 --end-date 2024-12-31`.
2. CLI parses inputs, constructs initial portfolio dict (cash, margin requirements, empty positions).
3. `BacktestEngine` coordinates the date iteration:
   - Increments date business day by business day.
   - Prefetches pricing, news, metrics, and insider trades to warm the cache.
   - Executes the compiled LangGraph agent DAG on the trailing 30-day window.
   - Converts final Portfolio Manager decisions into trades (buy, sell, short, cover).
   - Computes daily returns, Sharpe/Sortino ratios, and maximum drawdowns.
4. Outputs final performance metrics and trading logs to the console.

## Key Abstractions

**AgentState (`src/graph/state.py`):**
- Purpose: TypedDict representing state flowing between graph nodes.
- Keys:
  - `messages`: List of messages (Human, AI, System).
  - `data`: Dictionary holding tickers, start/end dates, current portfolio, and analyst signals.
  - `metadata`: Dictionary holding run config (provider, model, show_reasoning).

**AnalystConfig (`src/utils/analysts.py`):**
- Purpose: Single source of truth defining the available 18 analyst agents, their descriptions, styles, and backing agent functions.

**Model Factory (`src/llm/models.py`):**
- Purpose: LRU-cached factory function (`get_model`) returning a LangChain chat client instance mapped to the provider type. Prevents duplicate client instantiation.

## Error Handling

- **API Rate Limits:** `src/tools/api.py` traps HTTP 429 errors and retries requests using a full-jitter exponential backoff, complying with `Retry-After` headers if present.
- **DB Connection Leaks:** Web API endpoints call `db.close()` immediately after resolving keys, preventing active SQLite connections from remaining blocked during long-running streams.
- **Client Disconnection:** SSE endpoint runs a concurrent `wait_for_disconnect` task; if the HTTP connection drops, the async graph task is cancelled immediately.

## Cross-Cutting Concerns

- **Symmetric Encryption:** API keys are encrypted at-rest using `Fernet` (AES-128 in CBC mode) with key `DATABASE_ENCRYPTION_KEY` before database insertion.
- **Task Delegation:** Long-running flow runs can be offloaded asynchronously to Celery workers using Redis as the message broker.

---

*Architecture analysis: 2026-06-09*
*Update when major patterns change*
