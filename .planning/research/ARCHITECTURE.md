# Architecture Research

**Domain:** Hybrid Research Decision Engine for AI Hedge Fund
**Researched:** 2026-06-09
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph Workflow (DAG)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌─────────────────┐                     │
│  │ Regime Class │ ──> │ Agent Selector  │                     │
│  └──────────────┘    └────────┬────────┘                     │
│                               │                              │
│                               v                              │
│                      ┌─────────────────┐                     │
│                      │ Selected Agents │                     │
│                      └────────┬────────┘                     │
│                               │                              │
│                               v                              │
│                      ┌─────────────────┐                     │
│                      │   Safe Debate   │                     │
│                      └────────┬────────┘                     │
│                               │                              │
│                               v                              │
│                      ┌─────────────────┐                     │
│                      │ Consensus & Psy │                     │
│                      └────────┬────────┘                     │
│                               │                              │
│                               v                              │
│                      ┌─────────────────┐                     │
│                      │  Meta-Labeler   │                     │
│                      └────────┬────────┘                     │
│                               │                              │
│                               v                              │
│                      ┌─────────────────┐                     │
│                      │  Risk Manager   │                     │
│                      └────────┬────────┘                     │
│                               │                              │
│                               v                              │
│                      ┌─────────────────┐                     │
│                      │Portfolio Manager│                     │
│                      └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Regime Classifier | Classify volatility/trend context | Deterministic indicators on pricing window |
| Agent Selector | Select analysts dynamically based on regime | Matches config rules in `ANALYST_CONFIG` |
| Safe Debate | Bull/Bear debate and Red-Team risk critique | Sequential LLM agent invocations (flags-dependent) |
| Psy Guardrails | Calibrate confidence and flag herding | Heuristic formulas + dispersion calculations |
| Meta-Labeler | Assign allow/reduce/suppress/hold_only labels | Rules-based mapping from calibrated confidence |
| Risk Manager | Sizing scaling and final position limit checks | Deterministic multipliers on remaining limits |
| Portfolio Manager | Allowed actions and final execution decision | Constrains options before LLM final choice |

## Recommended Project Structure

```
src/
├── graph/                  # Workflow orchestration
│   ├── agent_selector.py   # Adaptive GoA selection
│   ├── regime_classifier.py# Market regime classifier
│   └── state.py            # TypedDict state with hybrid keys
├── agents/                 # Research and guardrail agents
│   ├── debate/             # Safe Debate layer
│   │   ├── bull_researcher.py
│   │   ├── bear_researcher.py
│   │   ├── risk_red_team.py
│   │   └── consensus.py    # Consensus agent
│   ├── psychological_guardrail.py # Overconfidence/herding check
│   └── meta_labeler.py     # Trade permission labeling
├── risk/                   # Deterministic calculations
│   ├── disagreement.py     # Disagreement and dispersion math
│   ├── drawdown_guardrail.py# CPPI drawdown floor math
│   └── sizing.py           # Multiplier combination logic
├── reflection/             # Evaluation and logging
│   ├── recorder.py         # JSONL trace writer
│   ├── evaluator.py        # Attribution scoring
│   └── schemas.py          # Reflection schemas
└── schemas/                # Shared model declarations
    └── hybrid.py           # Pydantic models for hybrid output
```

### Structure Rationale

- **src/graph/:** Keeps LangGraph orchestration and selector logic separate from agent prompt files.
- **src/agents/:** Segregates LLM agents (debate, guardrail, meta-labeler) from mathematical calculations.
- **src/risk/:** Contains pure Python math modules that have zero dependencies on LLMs or external agents, making them highly testable.
- **src/reflection/:** Isolates telemetry and backtest history recording to prevent leakage into trading decisions.

## Architectural Patterns

### Pattern 1: Deterministic Sizing Pipeline

**What:** Position sizing is computed by chaining fractional multipliers.
**When to use:** In risk managers and portfolio managers.
**Trade-offs:** Highly robust and predictable, but prevents LLMs from suggesting custom non-standard sizes.

```python
# Combined limit is a product of all deterministic constraints
combined_limit = (
    base_limit 
    * vol_multiplier 
    * disagreement_multiplier 
    * drawdown_multiplier 
    * meta_label_multiplier
)
```

### Pattern 2: Multi-Agent State Compaction

**What:** LangGraph state holds structured hybrid trace sub-keys to prevent message list bloating.
**When to use:** In State TypedDict schemas.
**Trade-offs:** Reduces token usage by only passing structured outputs downstream, but hides intermediate reasoning from general LLM view.

## Data Flow

### Request Flow

```
[Ticker Context] ──> [Regime Classifier] ──> [Agent Selector] ──> [Analyst DAG]
                                                                        │
                                                                        v
[Portfolio Manager] <── [Risk Manager] <── [Meta-Labeler] <── [Debate & Guardrails]
```

### Key Data Flows

1. **Analyst Signal Path:** Raw analyst signals are stored in `state["data"]["analyst_signals"]`, mapped to `GuardrailOutput`, passed to `MetaLabelOutput`, used to modify `combined_limit_pct` in `risk_manager.py`, and finally passed to `portfolio_manager.py` allowed actions.
2. **Reflection Telemetry Path:** At the end of each date iteration, the `BacktestEngine` sends the complete `HybridDecisionTrace` and portfolio state to `reflection.recorder.py` to write to JSONL.

## Scaling Considerations

- This is a local-first research tool. The primary scaling concern is API token usage and latency (running many LLM calls per day in a backtest).
- **Optimization:** Use cached models (`src/llm/models.py`), skip debate logic in simple regimes, and keep GoA selector max agents at 3-5 (using `--max-agents`).

## Anti-Patterns

### Anti-Pattern 1: Sizing in LLM Prompt
*What people do:* Ask the portfolio manager LLM "How many shares should we buy?".
*Why it's wrong:* LLMs cannot accurately count cash or track margin boundaries.
*Do this instead:* Compute deterministic `max_quantity` in Python, and only ask the LLM to choose an action from `allowed_actions`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Financial Datasets API | REST clients with caching | Cached local files under `data/` to avoid redundant hits |
| LLM Providers (OpenAI/Anthropic) | LangChain ChatModel | Must handle rate limiting (429) gracefully with exponential backoff |

---
*Architecture research for: Hybrid Research Decision Engine*
*Researched: 2026-06-09*
