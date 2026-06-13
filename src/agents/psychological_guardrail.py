"""Psychological Guardrail Agent — PSY-01.

Calibrates raw analyst signals for herding, overconfidence, and disagreement.
"""

import json
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from src.graph.state import AgentState, show_agent_reasoning
from src.risk.disagreement import compute_disagreement_score, compute_disagreement_multiplier
from src.schemas.hybrid import GuardrailOutput
from src.utils.llm import call_llm
from src.utils.progress import progress

# Agents that are NOT analysts — excluded from stance collection
_NON_ANALYST_AGENTS = frozenset({"risk_management_agent", "portfolio_management_agent"})

# Analysts whose signals are sentiment-heavy (increases subjectivity score)
_SENTIMENT_ANALYSTS = frozenset({"news_sentiment_analyst", "sentiment_analyst"})


class _GuardrailReasoning(BaseModel):
    reasoning: str


def psychological_guardrail_agent(state: AgentState, agent_id: str = "psychological_guardrail_agent"):
    """Calibrate analyst signals for psychological biases and disagreement."""
    data = state["data"]

    if not data.get("hybrid_mode", False):
        return {"messages": [], "data": {}}

    tickers = data["tickers"]
    analyst_signals = data.get("analyst_signals", {})
    guardrail_outputs: dict = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Collecting analyst stances")

        stances: list[int] = []
        confidences: list[int] = []
        sentiment_count = 0

        for analyst_key, signal_data in analyst_signals.items():
            if analyst_key in _NON_ANALYST_AGENTS:
                continue
            ticker_signal = signal_data.get(ticker) if isinstance(signal_data, dict) else None
            if not ticker_signal:
                continue
            raw_signal = ticker_signal.get("signal", "neutral")
            stances.append(1 if raw_signal == "bullish" else (-1 if raw_signal == "bearish" else 0))
            confidences.append(int(ticker_signal.get("confidence", 50)))
            if analyst_key in _SENTIMENT_ANALYSTS:
                sentiment_count += 1

        if not stances:
            guardrail_outputs[ticker] = GuardrailOutput(
                ticker=ticker,
                raw_confidence=50,
                disagreement_score=0.0,
                subjectivity_score=0.0,
                herding_flag=False,
                overconfidence_flag=False,
                calibrated_confidence=50,
                confidence_multiplier=1.0,
                risk_flags=[],
                reasoning="No analyst signals available.",
            ).model_dump()
            continue

        disagreement_score = compute_disagreement_score(stances)
        base_multiplier = compute_disagreement_multiplier(stances)
        n = len(stances)
        raw_confidence = int(sum(confidences) / n)

        herding_flag = (disagreement_score < 0.15) and (n >= 3) and (abs(sum(stances)) == n)
        overconfidence_flag = (raw_confidence > 80) and (disagreement_score < 0.2)
        subjectivity_score = round(min(sentiment_count / max(n, 1), 1.0), 4)

        penalty = 1.0
        risk_flags: list[str] = []
        if herding_flag:
            penalty *= 0.85
            risk_flags.append("herding_detected")
        if overconfidence_flag:
            penalty *= 0.90
            risk_flags.append("overconfidence_warning")
        if subjectivity_score > 0.3:
            penalty *= max(1.0 - subjectivity_score * 0.3, 0.7)
            risk_flags.append("high_subjectivity")

        final_multiplier = round(base_multiplier * penalty, 4)
        calibrated_confidence = max(0, min(100, int(raw_confidence * final_multiplier)))

        progress.update_status(agent_id, ticker, "Generating guardrail reasoning")
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a psychological risk guardrail for financial analysis. "
                "Return a brief 2-3 sentence reasoning string."
            )),
            ("human", (
                "Ticker: {ticker}\nStances: {stances}\nRaw confidence: {raw_confidence}\n"
                "Disagreement: {disagreement_score:.3f}\nHerding: {herding_flag}\n"
                "Overconfidence: {overconfidence_flag}\nFlags: {risk_flags}\n"
                "Calibrated confidence: {calibrated_confidence}"
            )),
        ])
        result = call_llm(
            prompt=prompt.format_messages(
                ticker=ticker, stances=stances, raw_confidence=raw_confidence,
                disagreement_score=disagreement_score, herding_flag=herding_flag,
                overconfidence_flag=overconfidence_flag, risk_flags=risk_flags,
                calibrated_confidence=calibrated_confidence,
            ),
            pydantic_model=_GuardrailReasoning,
            agent_name=agent_id,
            state=state,
        )

        guardrail_outputs[ticker] = GuardrailOutput(
            ticker=ticker,
            raw_confidence=raw_confidence,
            disagreement_score=round(disagreement_score, 4),
            subjectivity_score=subjectivity_score,
            herding_flag=herding_flag,
            overconfidence_flag=overconfidence_flag,
            calibrated_confidence=calibrated_confidence,
            confidence_multiplier=final_multiplier,
            risk_flags=risk_flags,
            reasoning=result.reasoning,  # type: ignore[attr-defined]
        ).model_dump()

        progress.update_status(
            agent_id, ticker,
            f"Calibrated: {calibrated_confidence} (raw: {raw_confidence}, mult: {final_multiplier:.3f})"
        )

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(guardrail_outputs, "Psychological Guardrail Agent")

    message = HumanMessage(content=json.dumps(guardrail_outputs), name=agent_id)
    return {
        "messages": [message],
        "data": {"guardrail_outputs": guardrail_outputs},
    }
