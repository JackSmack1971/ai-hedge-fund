# AI Developer Agent Prompt

Use this prompt when assigning implementation work to an AI coding agent.

---

You are working in the `JackSmack1971/ai-hedge-fund-forked` repository.

Your task is to implement the Hybrid Decision Engine documentation corpus under:

```text
docs/hybrid-decision-engine/
```

Read these files first, in order:

1. `README.md`
2. `architecture.md`
3. `module-contracts.md`
4. `implementation-roadmap.md`
5. `testing-and-validation.md`

## Project Goal

Upgrade the current AI Hedge Fund research/backtesting app with:

```text
Graph-of-Agents + Safe Debate + Psychological Guardrails + Risk-Constrained Portfolio Manager + Backtest Reflection
```

This must remain a local educational/research system. Do not add live trading, broker execution, or real-money automation.

## Current Codebase Anchors

Study these existing files before making changes:

```text
src/main.py
src/utils/analysts.py
src/agents/risk_manager.py
src/agents/portfolio_manager.py
src/backtesting/engine.py
src/backtesting/portfolio.py
src/utils/llm.py
```

The current design already has useful safety properties:

- analyst agents emit signals
- risk manager computes limits
- portfolio manager computes allowed actions
- portfolio state is mutated only by deterministic backtesting/trade execution code

Do not break those properties.

## Non-Negotiable Invariants

1. LLMs may reason, debate, critique, summarize, and produce structured signals.
2. LLMs must not directly mutate portfolio state.
3. LLMs must not directly set final share quantity without deterministic constraints.
4. Existing baseline CLI/backtester behavior must remain compatible.
5. All new hybrid behavior must be feature-flagged or safely optional.
6. Missing hybrid metadata must not crash old flows.
7. Suppressed or hold-only meta-labels must force hold.
8. Future returns must never be used during same-day decision generation.

## Preferred Implementation Order

Follow this sequence:

```text
1. Add shared schemas in `src/schemas/hybrid.py`.
2. Add deterministic risk utilities for disagreement and drawdown guardrails.
3. Add psychological guardrail agent.
4. Add consensus agent.
5. Add meta-labeler.
6. Integrate guardrail/meta-label multipliers into risk manager.
7. Integrate meta-label constraints into portfolio manager.
8. Add adaptive GoA selector and regime classifier.
9. Add bull/bear/risk Safe Debate expansion.
10. Add backtest reflection recorder.
```

Do not jump to the most complex parts first.

## First Pull Request Scope Recommendation

The first PR should be small:

```text
- `src/schemas/hybrid.py`
- `src/risk/disagreement.py`
- `src/risk/drawdown_guardrail.py`
- tests for schemas and deterministic risk utilities
```

Avoid modifying `src/main.py`, `risk_manager.py`, or `portfolio_manager.py` in the first PR unless absolutely necessary.

## Coding Style

- Prefer small modules over large rewrites.
- Use Pydantic models for structured LLM/intermediate outputs.
- Keep functions deterministic where possible.
- Fail closed: uncertainty should reduce risk, not increase it.
- Maintain backwards compatibility.
- Add tests for every deterministic utility.

## Forbidden First-Pass Work

Do not implement:

- live broker integration
- SAPPO or reinforcement-learning execution
- full Black-Litterman optimizer
- prompt self-modification
- automatic fine-tuning
- external paid data integrations
- hidden network dependencies in tests

## Expected First Output

Create a short implementation plan before editing code:

```text
Files to add:
Files to modify:
Tests to add:
Backward compatibility notes:
Risk/safety notes:
```

Then implement the smallest useful vertical slice.

## Definition of Done

A change is acceptable only if:

- tests pass
- existing CLI/backtester behavior remains intact
- new behavior is documented
- deterministic risk controls remain authoritative
- no LLM output can bypass risk or portfolio constraints
