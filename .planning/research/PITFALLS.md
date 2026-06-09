# Pitfalls Research

**Domain:** Hybrid Research Decision Engine for AI Hedge Fund
**Researched:** 2026-06-09
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Unconstrained LLM Quantity Mutation

**What goes wrong:**
An LLM agent outputs a raw trade quantity (e.g. "Buy 1000 shares") that exceeds available portfolio cash, breaches individual position limits, or ignores short-margin requirements.

**Why it happens:**
Developers trust the LLM to understand portfolio limits described in the system prompt without checking the outputs against live portfolio math.

**How to avoid:**
Enforce a hard separation: LLMs can only select from a set of pre-calculated `allowed_actions` (e.g. `buy`, `sell`, `hold`) and their chosen action is capped by a python-calculated `max_quantity` before execution.

**Warning signs:**
Backtest logs show negative cash, margin calls, or position sizes that exceed 100% of portfolio value.

**Phase to address:**
Phase 7 (Portfolio Manager Integration).

---

### Pitfall 2: Future Information Leakage in Reflection

**What goes wrong:**
The backtest engine records reflection metrics (like future 1-day/5-day/20-day returns) and the reflection system accidentally exposes these future returns to the active decision agents operating on the same date.

**Why it happens:**
Sharing a single database/context or using files that have historical data indexed by date.

**How to avoid:**
Ensure that during the decision-making step, only the current date window's data is readable. Reflection files can record outcome placeholders that are filled *offline* by a separate post-backtest evaluation script.

**Warning signs:**
Backtest accuracy is suspiciously high (e.g., 90%+ win rate) or agent confidence rises right before market spikes.

**Phase to address:**
Phase 9 (Backtest Reflection Recorder).

---

### Pitfall 3: Sentiment and Overconfidence Cascades (Herding)

**What goes wrong:**
Multiple analyst agents use similar base models and prompt structures, resulting in highly correlated but incorrect signals during market shocks, which leads to oversized positions.

**Why it happens:**
LLMs are highly prone to agreement cascades (herding) when reading the same sentiment news.

**How to avoid:**
Compute a deterministic signal disagreement score and standard deviation of agent confidences. Dampen the final position limit multiplier exponentially when agent disagreement is high or dispersion is low (indicating lockstep herding).

**Warning signs:**
All analysts output a buy signal with 95%+ confidence on a high-volatility news-shock day, leading to large drawdowns.

**Phase to address:**
Phase 3 (Psychological Guardrail Agent).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| In-process backtesting state | Easy to implement, fast | Hard to scale to concurrent users in web UI | Greenfield / Local development only |
| Static regime selection | Skip classifier mathematical coding | Fails to select appropriate analysts during market turns | Only during Phase 0 baseline verification |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| LLM Providers | 429 Rate limits during long backtests | Use local caching of LLM calls or implement backoff/retries |
| Financial APIs | Bypassing local data cache during backtests | Ensure prefetch cache is warmed up-front and queries are intercepted |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Large prefetch memory spike | Backend crash or high RAM use during 1-year run | Chunked prefetching or generator-based date iteration | Runs spanning > 3 tickers over 1+ years |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Bloated JSON trace in UI | Browser crashes when drawing large React Flow graphs | Compress or summarize metadata, keeping only key trace fields in UI payload |

## "Looks Done But Isn't" Checklist

- [ ] **Adaptive Selector:** Appears to work in static mode but fails to select different agents in adaptive mode. Verify by printing selected agent lists.
- [ ] **Drawdown Guardrail:** Appears to protect capital but permits trading at or below floor value. Verify with unit tests.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| LLM bypasses limits | HIGH | Audit portfolio state tracking, re-implement allowed action validation in `portfolio_manager.py`. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Unconstrained LLM Mutation | Phase 7 | Test with extremely high LLM confidence signals and verify quantities are capped. |
| Future Info Leakage | Phase 9 | Run backtester and inspect state dict to ensure future return keys do not exist before step finish. |
| Overconfidence Cascade | Phase 3 | Test with unanimous but incorrect analyst inputs, confirm confidence multiplier drops. |

---
*Pitfalls research for: Hybrid Research Decision Engine*
*Researched: 2026-06-09*
