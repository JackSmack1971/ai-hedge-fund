---
namespace: reports
created: 2026-05-22T12:05:00Z
updated: 2026-05-22T12:05:00Z
status: active
tags: report, session, code-quality, audit, security, tech-debt
---

# Session Report: 2026-05-22 — Code Quality & Maintainability Audit

## Task: Comprehensive code quality audit of ai-hedge-fund-forked (src/ + app/backend/)
## Outcome: complete

## Summary

A full static analysis audit was performed using radon (CC/MI), flake8, vulture, and bandit across all Python source files (src/: 12,908 LOC, app/backend/: 4,089 LOC). The audit found a codebase with critically high average cyclomatic complexity (D=22.1, threshold B=6), 20.8% code duplication in the agents directory, multiple security issues, and pervasive whitespace hygiene violations.

Six categories of findings were immediately patched: shell=True removed from subprocess calls (Bandit HIGH B602), request timeouts added (Bandit HIGH B113), 7 bare except: clauses replaced with except Exception:, 9 unused imports removed from main.py, 1 mutable default argument fixed, and 15 broken f-strings (F541) fixed. 52 existing tests pass post-fix with no regressions.

12 GitHub Issues (#236–#247) were filed for all remaining audit findings that require larger refactors: the catastrophically complex charlie_munger functions (CC=93/44/42), cathie_wood complexity (CC=51/39), get_model nesting depth=11, duplicated analyze_sentiment/analyze_insider_activity across 3 agents, and whitespace hygiene.

## Files Created or Modified in the Repo

- `src/utils/ollama.py` — Removed shell=True from 2 subprocess calls + fixed F541
- `src/tools/api.py` — Added (10,30)s timeout to all requests; replaced 5 bare except: with except Exception:
- `src/main.py` — Removed 9 unused imports; fixed mutable default arg selected_analysts=[]→None
- `src/llm/models.py` — Removed f prefix from 10 broken f-strings (F541)
- `src/agents/aswath_damodaran.py` — Fixed 1 F541 f-string
- `src/agents/phil_fisher.py` — Fixed 3 F541 f-strings

## Files Written or Updated in ./memory/

- `journal/2026-05-22--code-quality-audit-start.md` — Audit kickoff, all findings
- `discoveries/code-quality-audit-2026-05-22.md` — Quantified discovery record
- `reports/session-2026-05-22--code-quality-audit.md` — This report

## GitHub Issues Touched

- #236 — filed: charlie_munger CC=93 unmaintainable
- #237 — filed: 15 broken f-strings (F541) — partially fixed this turn
- #238 — filed: 20.8% duplication in agents/ (analyze_sentiment x3, analyze_insider_activity x3)
- #239 — filed: get_model CC=41 / nesting=11
- #240 — filed: shell=True Bandit HIGH — fixed this turn
- #241 — filed: 7 bare except: fail-open — fixed this turn
- #242 — filed: requests without timeout Bandit HIGH — fixed this turn
- #243 — filed: mutable default argument — fixed this turn
- #244 — filed: dead code 8 unused imports in main.py — fixed this turn
- #245 — filed: cathie_wood CC=51/39
- #246 — filed: average CC D (22.1) codebase-wide
- #247 — filed: whitespace hygiene 614 violations W291/W293

## Decisions Made

- Fixed shell=True in subprocess by removing the flag (list-form args are safe without shell).
- Fixed bare except: to except Exception: (not more specific, because callers return empty list regardless).
- Fixed mutable default by changing to None sentinel (matching existing create_workflow pattern).
- Did NOT refactor charlie_munger/cathie_wood/get_model — blast radius too large for single turn without operator approval.

## Failures

None during fix application.

## Successes

- 52 tests pass post-fix
- All F541, F401 (main.py), E722 (api.py), B602 violations eliminated
- Bandit reports "No issues identified" for B602 in ollama.py
- Commit 2e1804d pushed to claude/magical-meitner-GvLo7

## FSV Evidence

```
=== F541 ALL === CLEAN
=== E722 in api.py === CLEAN
=== F401 in main.py === CLEAN
bandit src/utils/ollama.py -t B602: No issues identified.
timeout=_TIMEOUT at api.py:46,48: CONFIRMED
52 tests passed, 0 failures
```

## Open Blockers

None.

## Resume Here Next Session

- Start by reading: `./memory/discoveries/code-quality-audit-2026-05-22.md` for full finding list
- Priority open items:
  1. #236 — charlie_munger refactor (CC=93/44/42) — requires decomposing 3 functions
  2. #238 — Extract analyze_sentiment + analyze_insider_activity to shared module
  3. #239 — Refactor get_model to registry pattern (CC=41 → CC=2)
  4. #245 — cathie_wood refactor (CC=51/39)
  5. #247 — Run black formatter to fix 614 whitespace violations
- Watch out for: poetry venv doesn't have all deps installed; use `poetry run pytest` not bare `pytest`
- Open question: whether #246 (avg CC D=22.1) should have a radon CI gate added alongside the existing test/lint CI

## Confidence: high
All changes verified by FSV (flake8/bandit re-run + 52 tests pass). Issue numbers confirmed from GitHub API responses.
