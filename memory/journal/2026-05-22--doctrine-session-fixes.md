---
namespace: journal
created: 2026-05-22T15:00:00Z
updated: 2026-05-22T15:00:00Z
status: active
tags: bug-fixes, session, doctrine, ordering, cache, llm, warren-buffett
---

# Journal: 2026-05-22 — Doctrine Session Bug Fixes

## Session Branch
`claude/ai-coding-agent-doctrine-gNd1R`

## Issues Closed This Session

### Already-fixed issues (closed with evidence):
- #240 shell=True (fixed in PR #248)
- #241 bare except: (fixed in PR #248)
- #242 requests timeout (fixed in PR #248)
- #243 mutable default arg (fixed in PR #248)
- #244 unused imports (fixed in PR #248)

### Fixed in this session:
- #154 — analysts.py duplicate order=6 → renumbered peter_lynch+10 entries to 7-17
- #133 — technicals.py calculate_adx mutates DataFrame → df.copy() fix
- #155 — llm.py double-negative condition → use_json_mode named boolean
- #158 — api.py cache key mismatch → ticker-only key + date-range filter
- #134 — warren_buffett.py analyze_pricing_power always 0 → gross_profit/revenue
- #135 — warren_buffett.py max_possible_score wrong → added max_score keys
- #205 — SQLAlchemy deprecated import → sqlalchemy.orm.declarative_base
- #222 — pyproject.toml black line-length 420 → 120

## Test Status
295 tests pass, coverage 41.20%
Commits: d9b168e, 84754d9, 4c7b1c5, 9ef12f7

## Lessons Learned
- PriceResponse model requires 'ticker' field in mock data (not just 'prices')
- calculate_adx stores results as item[0]=newest, item[-1]=oldest (reversed chronological)
- Never use -W error::DeprecationWarning globally — third-party libs (langchain_gigachat) emit Pydantic V2 warnings

## What's Left (priority)
- Many p2/p3 bugs still open in the queue
- #196 [p1] backend test coverage — assigned to JackSmack1971, skip
- #236 charlie_munger CC=93 — large refactor, multi-turn work
- Performance issues (#159 O(n²), #162 LLM instance cache, #163 prefetch)
- Config issues (#219 DB URL hardcoded, #220 CORS hardcoded, #221 ollama:latest)
