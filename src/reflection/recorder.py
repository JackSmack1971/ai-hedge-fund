"""Reflection recorder for hybrid decision traces (ROUT-03).

Records structured JSONL traces of hybrid engine decisions for offline
outcome evaluation and attribution analysis.

Each record is a serialized HybridDecisionTrace (one per ticker per run/date).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.schemas.hybrid import (
    DebateOutput,
    GuardrailOutput,
    HybridDecisionTrace,
    MetaLabelOutput,
    RegimeClassification,
)


def record_trace(output_path: str | Path, date: str, final_state: dict) -> None:
    """Extract HybridDecisionTrace records from final agent state and append to JSONL.

    Args:
        output_path: Path to the output .jsonl file (created/appended).
        date: ISO date string for this run (e.g., "2024-03-15").
        final_state: The final AgentState dict returned by agent.invoke().
    """
    data = final_state.get("data", {})
    tickers = data.get("tickers", [])
    for ticker in tickers:
        trace = _build_trace(ticker, date, data)
        _append_jsonl(output_path, trace.model_dump(mode="json"))


def _build_trace(ticker: str, date: str, data: dict) -> HybridDecisionTrace:
    """Construct a HybridDecisionTrace from state data for a single ticker."""
    timestamp = _parse_date(date)

    regime_raw = data.get("regime_classification", {}).get(ticker)
    guardrail_raw = data.get("guardrail_outputs", {}).get(ticker)
    meta_raw = data.get("meta_label_outputs", {}).get(ticker)
    debate_raw = data.get("debate_outputs", {}).get(ticker)
    selected = data.get("regime_selection", {}).get(ticker, [])

    regime = _safe_construct(RegimeClassification, regime_raw)
    guardrails = _safe_construct(GuardrailOutput, guardrail_raw)
    meta_label = _safe_construct(MetaLabelOutput, meta_raw)
    debate = _safe_construct(DebateOutput, debate_raw)

    reasoning_summary = _build_summary(ticker, data, regime_raw, guardrail_raw, meta_raw)

    return HybridDecisionTrace(
        ticker=ticker,
        timestamp=timestamp,
        regime=regime,
        selected_agents=selected,
        debate=debate,
        guardrails=guardrails,
        meta_label=meta_label,
        reasoning_summary=reasoning_summary,
    )


def _safe_construct(model_class, raw: Any | None):
    """Construct a Pydantic model from a dict, returning None on failure."""
    if raw is None or not isinstance(raw, dict):
        return None
    try:
        return model_class(**raw)
    except Exception:
        return None


def _parse_date(date_str: str) -> datetime | None:
    """Parse ISO date string to datetime, returning None on failure."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _build_summary(
    ticker: str, data: dict, regime_raw: dict | None, guardrail_raw: dict | None, meta_raw: dict | None
) -> str:
    """Build a concise human-readable reasoning summary for a ticker trace."""
    parts = [f"ticker={ticker}"]
    if regime_raw:
        parts.append(f"regime={regime_raw.get('regime', '?')}({regime_raw.get('confidence', 0)}%)")
    if guardrail_raw:
        parts.append(
            f"calibrated_conf={guardrail_raw.get('calibrated_confidence', '?')} "
            f"multiplier={guardrail_raw.get('confidence_multiplier', '?'):.2f}"
            if isinstance(guardrail_raw.get('confidence_multiplier'), float)
            else f"calibrated_conf={guardrail_raw.get('calibrated_confidence', '?')}"
        )
    if meta_raw:
        parts.append(f"label={meta_raw.get('label', '?')} allow_trade={meta_raw.get('allow_trade', '?')}")
    return " | ".join(parts)


def _append_jsonl(path: str | Path, record: dict) -> None:
    """Append a single JSON record as a line to the JSONL file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


class ReflectionRecorder:
    """Stateful recorder that accumulates traces across multiple run_hedge_fund calls.

    Usage:
        recorder = ReflectionRecorder("traces/2024.jsonl")
        for date in dates:
            final_state = agent.invoke(...)
            recorder.record(date, final_state)
    """

    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._count = 0

    def record(self, date: str, final_state: dict) -> int:
        """Record traces for all tickers in the final state. Returns number of traces written."""
        data = final_state.get("data", {})
        tickers = data.get("tickers", [])
        before = self._count
        for ticker in tickers:
            trace = _build_trace(ticker, date, data)
            _append_jsonl(self.output_path, trace.model_dump(mode="json"))
            self._count += 1
        return self._count - before

    @property
    def total_traces(self) -> int:
        return self._count
