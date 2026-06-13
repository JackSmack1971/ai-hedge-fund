"""Consensus Agent — DEBT-01.

Summarizes analyst signals into dominant/minority stances, consensus
confidence, and unresolved conflicts for a given ticker.
"""

import json
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from src.graph.state import AgentState, show_agent_reasoning
from src.utils.llm import call_llm
from src.utils.progress import progress

_NON_ANALYST_AGENTS = frozenset({"risk_management_agent", "portfolio_management_agent"})


class ConsensusReport(BaseModel):
    dominant_stance: Literal["bullish", "bearish", "neutral"]
    dominant_count: int = Field(ge=0)
    minority_stances: List[str]
    consensus_confidence: int = Field(ge=0, le=100)
    unresolved_conflicts: List[str]
    summary: str


class _ConsensusSummaryOnly(BaseModel):
    """Narrow model for LLM call — only narrative fields the LLM should provide."""
    unresolved_conflicts: List[str]
    summary: str


def consensus_agent(state: AgentState, agent_id: str = "consensus_agent"):
    """Aggregate analyst signals into a structured consensus report per ticker."""
    data = state["data"]

    if not data.get("hybrid_mode", False):
        return {"messages": [], "data": {}}

    tickers = data["tickers"]
    analyst_signals = data.get("analyst_signals", {})
    consensus_output: dict = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Tallying analyst votes")

        votes: dict[str, int] = {"bullish": 0, "bearish": 0, "neutral": 0}
        confidences_by_stance: dict[str, list[int]] = {"bullish": [], "bearish": [], "neutral": []}

        for analyst_key, signal_data in analyst_signals.items():
            if analyst_key in _NON_ANALYST_AGENTS:
                continue
            ticker_signal = signal_data.get(ticker) if isinstance(signal_data, dict) else None
            if not ticker_signal:
                continue
            signal = ticker_signal.get("signal", "neutral")
            stance = signal if signal in votes else "neutral"
            votes[stance] += 1
            confidences_by_stance[stance].append(int(ticker_signal.get("confidence", 50)))

        total = sum(votes.values())
        if total == 0:
            consensus_output[ticker] = ConsensusReport(
                dominant_stance="neutral",
                dominant_count=0,
                minority_stances=[],
                consensus_confidence=50,
                unresolved_conflicts=[],
                summary="No analyst signals available.",
            ).model_dump()
            continue

        max_count = max(votes.values())
        leaders = [s for s, c in votes.items() if c == max_count]
        dominant_stance = leaders[0] if len(leaders) == 1 else "neutral"
        dominant_count = votes[dominant_stance] if dominant_stance != "neutral" else max_count
        minority_stances = [s for s, c in votes.items() if c > 0 and s != dominant_stance]
        dom_confidences = confidences_by_stance[dominant_stance]
        consensus_confidence = int(sum(dom_confidences) / len(dom_confidences)) if dom_confidences else 50

        progress.update_status(agent_id, ticker, "Generating consensus summary")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a consensus analyst. Summarize analyst signals concisely."),
            ("human", (
                "Ticker: {ticker}\nVotes: {votes}\nDominant: {dominant_stance} ({dominant_count}/{total})\n"
                "Minority: {minority_stances}\nConsensus confidence: {consensus_confidence}\n\n"
                "Return a ConsensusReport with: dominant_stance, dominant_count, minority_stances, "
                "consensus_confidence, unresolved_conflicts (list key disagreements), summary (2 sentences)."
            )),
        ])
        result = call_llm(
            prompt=prompt.format_messages(
                ticker=ticker, votes=votes, dominant_stance=dominant_stance,
                dominant_count=dominant_count, total=total,
                minority_stances=minority_stances, consensus_confidence=consensus_confidence,
            ),
            pydantic_model=_ConsensusSummaryOnly,
            agent_name=agent_id,
            state=state,
        )
        consensus_output[ticker] = ConsensusReport(
            dominant_stance=dominant_stance,  # type: ignore[arg-type,attr-defined]
            dominant_count=dominant_count,
            minority_stances=minority_stances,
            consensus_confidence=consensus_confidence,
            unresolved_conflicts=result.unresolved_conflicts,  # type: ignore[attr-defined]
            summary=result.summary,  # type: ignore[attr-defined]
        ).model_dump()

        progress.update_status(agent_id, ticker, f"Consensus: {dominant_stance} ({dominant_count}/{total})")

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(consensus_output, "Consensus Agent")

    message = HumanMessage(content=json.dumps(consensus_output), name=agent_id)
    return {
        "messages": [message],
        "data": {"consensus_output": consensus_output},
    }
