---
namespace: context
created: 2026-05-21T00:00:00Z
updated: 2026-05-21T00:00:00Z
status: active
tags: mission, testing, github-issues
---

# Mission Brief

## Task
Complete all 10 open GitHub issues (all testing-related) for the ai-hedge-fund-forked repo.

## Branch
`claude/complete-github-issues-f1Ikr`

## Issues (in priority order)
- #122 (critical): Agent unit test harness for all 21 analyst agents
- #123 (critical): FastAPI backend route tests
- #124 (critical): Backend repository and database layer tests
- #125 (critical): API data fetching and response parsing tests
- #126 (high): Data cache merge, deduplication, and eviction tests
- #127 (high): CLI input parsing and validation tests
- #128 (high): LLM model provider selection tests
- #129 (high): Expand backtesting edge case coverage
- #130 (medium): Add pytest-cov and enforce minimum coverage threshold
- #131 (medium): Add GitHub Actions CI workflow

## Key Codebase Facts
- Python project with poetry; src/ layout
- src/agents/ - 21 analyst agents
- src/tools/api.py - data fetching
- src/data/cache.py - in-memory cache
- src/data/models.py - Pydantic models
- src/llm/models.py - LLM provider config
- src/cli/input.py - CLI input parsing
- src/backtesting/ - backtesting engine
- app/backend/ - FastAPI backend
- tests/ existing: test_api_rate_limiting.py, backtesting/ tests, fixtures/api/
