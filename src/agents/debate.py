"""Safe Debate Agent — DEBT-02.

Runs three sequential LLM agents (BullResearcher, BearResearcher, RiskRedTeam)
per ticker when debate_mode is True.
"""

import json
from typing import List

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.graph.state import AgentState, show_agent_reasoning
from src.schemas.hybrid import DebateOutput
from src.utils.llm import call_llm
from src.utils.progress import progress


class _BullCase(BaseModel):
    bull_case: str = Field(description="Strongest bullish argument")


class _BearCase(BaseModel):
    bear_case: str = Field(description="Strongest bearish argument")


class _RedTeam(BaseModel):
    risk_red_team: str = Field(description="Critical attack on both cases")
    unresolved_conflicts: List[str] = Field(description="Key unresolved conflicts")
    debate_confidence: int = Field(ge=0, le=100, description="Resulting debate confidence")


def debate_agent(state: AgentState, agent_id: str = "debate_agent"):
    """Run a Bull/Bear/RedTeam debate per ticker when debate_mode is enabled."""
    data = state["data"]

    if not data.get("hybrid_mode", False):
        return {"messages": [], "data": {}}

    tickers = data["tickers"]
    analyst_signals = data.get("analyst_signals", {})
    debate_mode = data.get("debate_mode", False)
    debate_outputs: dict = {}

    for ticker in tickers:
        if not debate_mode:
            debate_outputs[ticker] = None
            continue

        # Collect analyst summaries for context
        ticker_summaries = []
        for analyst_key, signal_data in analyst_signals.items():
            ticker_signal = signal_data.get(ticker) if isinstance(signal_data, dict) else None
            if ticker_signal:
                signal = ticker_signal.get("signal", "neutral")
                conf = ticker_signal.get("confidence", 50)
                ticker_summaries.append(f"{analyst_key}: {signal} ({conf}%)")
        context = "\n".join(ticker_summaries) if ticker_summaries else "No analyst signals."

        # Step 1: Bull Researcher
        progress.update_status(agent_id, ticker, "Bull Researcher")
        bull_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Bull Researcher. Write the strongest possible bullish case."),
            ("human", "Ticker: {ticker}\nAnalyst signals:\n{context}\n\nWrite the strongest bull case."),
        ])
        bull_result = call_llm(
            prompt=bull_prompt.format_messages(ticker=ticker, context=context),
            pydantic_model=_BullCase, agent_name=agent_id, state=state,
        )

        # Step 2: Bear Researcher
        progress.update_status(agent_id, ticker, "Bear Researcher")
        bear_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Bear Researcher. Write the strongest possible bearish case."),
            ("human", "Ticker: {ticker}\nAnalyst signals:\n{context}\n\nWrite the strongest bear case."),
        ])
        bear_result = call_llm(
            prompt=bear_prompt.format_messages(ticker=ticker, context=context),
            pydantic_model=_BearCase, agent_name=agent_id, state=state,
        )

        # Step 3: Risk Red Team
        progress.update_status(agent_id, ticker, "Risk Red Team")
        red_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Risk Red-Team analyst. Critically attack both cases and identify conflicts."),
            ("human", (
                "Ticker: {ticker}\nBull case: {bull_case}\nBear case: {bear_case}\n\n"
                "Attack both cases, list unresolved conflicts, and give a debate confidence score."
            )),
        ])
        red_result = call_llm(
            prompt=red_prompt.format_messages(
                ticker=ticker, bull_case=bull_result.bull_case, bear_case=bear_result.bear_case,  # type: ignore[attr-defined]
            ),
            pydantic_model=_RedTeam, agent_name=agent_id, state=state,
        )

        debate_outputs[ticker] = DebateOutput(
            ticker=ticker,
            bull_case=bull_result.bull_case,  # type: ignore[attr-defined]
            bear_case=bear_result.bear_case,  # type: ignore[attr-defined]
            risk_red_team=red_result.risk_red_team,  # type: ignore[attr-defined]
            unresolved_conflicts=red_result.unresolved_conflicts,  # type: ignore[attr-defined]
            debate_confidence=red_result.debate_confidence,  # type: ignore[attr-defined]
        ).model_dump()

        progress.update_status(agent_id, ticker, f"Debate complete ({len(red_result.unresolved_conflicts)} conflicts)")  # type: ignore[attr-defined]

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(debate_outputs, "Safe Debate Agent")

    message = HumanMessage(content=json.dumps(debate_outputs, default=str), name=agent_id)
    return {
        "messages": [message],
        "data": {"debate_outputs": debate_outputs},
    }
