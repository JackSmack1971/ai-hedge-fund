# Stack Research

**Domain:** Hybrid Research Decision Engine for AI Hedge Fund
**Researched:** 2026-06-09
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11 | Backend service, agent logic, backtests, CLI | Codebase primary language. Fast, rich math libraries, standard for LLM orchestrations. |
| LangGraph | 0.3.0 | Orchestrates multi-agent research DAG workflow |中央 routing mechanism for Graph-of-Agents and debate loops. |
| FastAPI | 0.104.0 | Backend REST API server | High-performance async routing and Server-Sent Events (SSE) streaming support. |
| Pydantic | 2.x | Structured data schemas and model validation | Crucial for enforcing strict types and contracts between LLMs and deterministic code. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pandas | 2.1.0 | Pricing and financial data manipulation | Volatility/correlation calculation, backtest loop alignment. |
| Numpy | 2.x | Numerical calculations | Computing standard deviation, variance, and portfolio cushion. |
| Cryptography (Fernet) | 41.x | Encrypting external API keys at rest | Saving user financial datasets or LLM API keys in SQLite database. |
| Celery | 5.4.0 | Offloading long-running backtest runs | Running asynchronous jobs (web UI runs). |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Poetry | Python dependency management |centralized in `pyproject.toml` and `poetry.lock`. |
| Black | Code formatting | Enforces standard style guidelines across `src` and `app`. |
| Pytest | Backend test suite execution | Used to write unit tests for schemas and deterministic utilities. |

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Pydantic | Marshmallow | If Pydantic is not supported by LangGraph (unlikely, as LangGraph integrates natively with Pydantic). |
| LangGraph | AutoGen | AutoGen is better for fully conversational agents, but LangGraph is better for controlled, structured research pipelines. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Direct LLM Quantity Generation | LLMs are prone to hallucinating extreme quantities or bypassing risk parameters | Deterministic portfolio sizing math |
| SQLite concurrent writes without WAL | Lock errors on concurrent web app sessions | SQLite in WAL mode or PostgreSQL in production |

## Stack Patterns by Variant

**If Adaptive GoA Mode Active:**
- Use regime-specific subagent routing based on central registry mapping.
- Because it saves LLM tokens and focuses analysis on relevant investment philosophies.

**If Safe Debate Active:**
- Spawn Bull Researcher, Bear Researcher, and Risk Red-Team nodes in sequence before consensus synthesis.
- Because it confronts confirmation bias before confidence calibration.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| langchain-openai@0.3.5 | langchain@0.3.7 | Main LLM integration |
| pydantic@2.x | langgraph@0.3.0 | Schema validation in state transitions |

## Sources

- [docs/hybrid-decision-engine/module-contracts.md](file:///c:/workspaces/ai-hedge-fund-forked/docs/hybrid-decision-engine/module-contracts.md) — schema requirements.
- [docs/hybrid-decision-engine/architecture.md](file:///c:/workspaces/ai-hedge-fund-forked/docs/hybrid-decision-engine/architecture.md) — design principles.

---
*Stack research for: Hybrid Research Decision Engine*
*Researched: 2026-06-09*
