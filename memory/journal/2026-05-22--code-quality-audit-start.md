---
namespace: journal
created: 2026-05-22T11:45:00Z
updated: 2026-05-22T11:45:00Z
status: active
tags: audit, code-quality, cyclomatic-complexity, duplication, security, debt
---

# Journal: 2026-05-22 — Code Quality & Maintainability Audit

## Session Intent
Task: Comprehensive code quality & maintainability audit of ai-hedge-fund-forked.
Context: src/ (12,908 LOC), app/backend/ (4,089 LOC). Previous sessions handled testing.
Constraints: §25 Code Quality Doctrine + §1 cardinal rules. File issues for all findings not fixed this turn.
Done When: All findings quantified, issues filed, session report written.
FSV Strategy: radon CC/MI, flake8, vulture, bandit — cross-referenced with manual spot-checks.

## Tools Run
- radon cc (cyclomatic complexity): 28 files analyzed
- radon mi (maintainability index): 54 files analyzed
- flake8 --statistics: full src/ and app/backend/
- vulture --min-confidence 80: dead code
- bandit -r -ll: security SAST
- Manual nesting-depth AST scan: 20 worst functions

## Key Metrics

| Metric | Value |
|--------|-------|
| Total LOC (src/) | 12,908 |
| Total LOC (app/backend/) | 4,089 |
| Avg CC (src/): | D (22.1) — threshold: B=6 |
| Files with F-rated functions | 3 (charlie_munger, cathie_wood, llm/models) |
| Highest CC single function | 93 (charlie_munger.analyze_management_quality) |
| Lowest MI score | 7.76/100 (charlie_munger.py) |
| Code duplication rate (agents/) | 20.8% |
| Flake8 total violations (src/) | ~1,000 |
| Bare except clauses | 7 |
| Unused imports (F401) | 17 |
| Broken f-strings (F541) | 15 |
| Unused variables (F841) | 7 |
| Bandit HIGH severity | 3 (os.system, subprocess shell=True x2) |

## Critical Findings (filing as issues)

### CC=93 — charlie_munger.analyze_management_quality
File: src/agents/charlie_munger.py:268
Complexity: F (93) — catastrophically high. Threshold for "unmaintainable" is E (30+).
MI: 7.76 (C grade — all other files are A).

### CC=51 — cathie_wood.analyze_innovation_growth
File: src/agents/cathie_wood.py:210

### CC=41, depth=11 — get_model in llm/models.py
File: src/llm/models.py:138. 11 levels of if/elif nesting for 11 LLM providers.

### 20.8% Duplication — analyze_sentiment/analyze_insider_activity copied 3×
Files: peter_lynch.py:365, phil_fisher.py:503, stanley_druckenmiller.py:320
and: peter_lynch.py:396, phil_fisher.py:461, stanley_druckenmiller.py:273

### 15 Broken f-strings (F541) — 10 in llm/models.py
Files: llm/models.py:143,152,158,164,170,185,206,224,230,236
aswath_damodaran.py:277, phil_fisher.py:286,288,396, llm/models.py:143

### 7 bare except: clauses (fail-open)
Files: tools/api.py (5), warren_buffett.py:423, valuation.py:390

### SEC: subprocess with shell=True — Bandit HIGH
Files: utils/ollama.py:49, utils/ollama.py:95

### SEC: os.system() — Bandit HIGH
File: utils/display.py:260

### SEC: requests without timeout
File: tools/api.py:45, tools/api.py:47

### Mutable default argument — run_hedge_fund()
File: src/main.py:52 — `selected_analysts: list[str] = []`

### Dead code — 8 unused imports in main.py
File: src/main.py — sys, Fore, Style, questionary, ANALYST_ORDER, save_graph_as_png, argparse, datetime, relativedelta

## Status
Filing GitHub Issues now.
