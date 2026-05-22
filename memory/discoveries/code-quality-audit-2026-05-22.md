---
namespace: discoveries
created: 2026-05-22T12:00:00Z
updated: 2026-05-22T12:00:00Z
status: active
tags: code-quality, cyclomatic-complexity, duplication, security, tech-debt
---

# Discovery: Comprehensive Code Quality Audit — 2026-05-22

## Key Metrics (verified by radon, flake8, vulture, bandit)

| Metric | Measured Value | Industry Threshold |
|--------|---------------|-------------------|
| Avg cyclomatic complexity (src/) | D (22.1) | B (6) |
| Worst MI score | 7.76/100 — charlie_munger.py | A (>65) |
| Code duplication (agents/) | 20.8% | <5% |
| F-rated functions (CC≥41) | 5 | 0 |
| E-rated functions (CC≥30) | 4 | 0 |
| Bare except: clauses (FIXED) | 7 | 0 |
| Broken f-strings F541 (FIXED) | 15 | 0 |
| Unused imports F401 in main.py (FIXED) | 9 | 0 |
| shell=True subprocess (FIXED) | 2 | 0 |
| requests without timeout (FIXED) | 2 | 0 |
| Mutable default arg (FIXED) | 1 | 0 |
| Whitespace violations W291/W293 | 614 | 0 |

## Critical Unfixed Issues (filed as GitHub Issues)

### charlie_munger.py — CC=93 worst function (Issue #236)
- analyze_management_quality: F (93)
- analyze_predictability: F (44)  
- analyze_moat_strength: F (42)
- File MI: 7.76 (only C-grade file in project)

### Code Duplication (Issue #238)
- analyze_sentiment: 3 copies (peter_lynch, phil_fisher, stanley_druckenmiller)
- analyze_insider_activity: 3 copies (same 3 files)
- 20.8% duplication rate in agents/

### get_model in llm/models.py (Issue #239)
- CC=41 (F-rated), nesting depth=11
- 90-line if/elif chain for 11 LLM providers

### cathie_wood.py (Issue #245)
- analyze_innovation_growth: CC=51 (F-rated)
- analyze_disruptive_potential: CC=39 (E-rated)

## What Was Fixed This Session

1. shell=True removed from utils/ollama.py (2 locations)
2. Request timeout (10,30)s added to tools/api.py
3. 7 bare except: → except Exception: in tools/api.py
4. 9 unused imports removed from main.py
5. Mutable default arg fixed in run_hedge_fund()
6. 15 broken f-strings (F541) fixed across 3 files

## Related
- See also: ./memory/reports/session-2026-05-22--code-quality-audit.md
- GitHub Issues: #236, #237, #238, #239, #240, #241, #242, #243, #244, #245, #246, #247
