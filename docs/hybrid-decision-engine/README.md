# Hybrid Decision Engine Documentation Corpus

## Purpose

This documentation corpus defines the implementation target for upgrading the current AI Hedge Fund fork into a hybrid research decision engine built around:

- Graph-of-Agents adaptive analyst routing
- Safe Debate thesis confrontation
- Psychological Guardrails for bias, disagreement, and confidence calibration
- Risk-Constrained Portfolio Management
- Backtest Reflection and attribution memory

The goal is not to create a live trading system. The goal is to create a stronger local-first research and backtesting system where LLMs generate, challenge, and synthesize investment theses, while deterministic math and risk controls retain final authority over sizing, admissibility, and execution simulation.

## Core Design Principle

LLMs may reason, debate, summarize, and critique.

Deterministic code must control:

- trade admissibility
- maximum quantity
- risk limits
- drawdown controls
- portfolio exposure
- backtest accounting
- confidence adjustment
- calibration metrics

No LLM output should directly create an unconstrained trade.

## Current Codebase Anchor Points

The current system already has a useful foundation:

- `src/main.py` builds the LangGraph workflow.
- `src/utils/analysts.py` defines the analyst registry and agent metadata.
- `src/agents/risk_manager.py` computes volatility/correlation-adjusted position limits.
- `src/agents/portfolio_manager.py` computes allowed actions and constrains final trade choices.
- `src/backtesting/engine.py` coordinates the backtest loop.
- `src/backtesting/portfolio.py` tracks cash, long/short positions, margin, and realized gains.

## Documentation Map

Read these files in order:

1. `architecture.md` — target architecture and data flow.
2. `module-contracts.md` — exact modules, schemas, responsibilities, and forbidden behaviors.
3. `implementation-roadmap.md` — phased implementation sequence for an AI coding agent.
4. `testing-and-validation.md` — test plan, backtest validation, calibration metrics, and regression expectations.
5. `agent-developer-prompt.md` — task prompt for the AI developer agent.

## Non-Goals

Do not implement these in the first integration pass:

- real-money trading
- broker execution
- reinforcement-learning execution engines
- order-book simulation
- full institutional Black-Litterman optimization
- fine-tuned financial LLMs
- Bloomberg/FactSet/Refinitiv ingestion
- automatic self-modifying prompts

These may remain future research topics, but they are intentionally out of scope for the first practical implementation.

## Target First Release

The first useful release should add a hybrid decision layer that can run inside existing CLI/backtester flows:

```text
selected ticker context
  -> market regime classifier
  -> adaptive GoA analyst selector
  -> selected analyst agents
  -> bull/bear/risk debate layer
  -> psychological guardrail layer
  -> consensus/meta-label output
  -> risk manager
  -> constrained portfolio manager
  -> backtest reflection recorder
```

## Safety Rule

Every new AI-generated signal must be converted into a structured intermediate output and passed through deterministic validation before affecting portfolio state.

## Status

This corpus is a forward-looking design spec, not a description of the current runtime surface. Use it as target-state documentation only; do not treat it as evidence of implemented behavior.
