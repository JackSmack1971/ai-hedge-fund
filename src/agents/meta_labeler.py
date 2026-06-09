"""Meta-Labeler Agent — META-01.

Maps guardrail calibration outputs to trade permission labels using
deterministic priority rules (suppress > hold_only > reduce > allow).
"""

import json

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from src.graph.state import AgentState, show_agent_reasoning
from src.schemas.hybrid import MetaLabelOutput
from src.utils.llm import call_llm
from src.utils.progress import progress


class _MetaReasoning(BaseModel):
    reasoning: str


# Deterministic rule thresholds (D-23)
_SUPPRESS_CONFIDENCE = 30
_SUPPRESS_MULTIPLIER = 0.40
_HOLD_ONLY_CONFIDENCE = 50
_HOLD_ONLY_MULTIPLIER = 0.60
_REDUCE_CONFLICTS = 3


def meta_labeler_agent(state: AgentState, agent_id: str = "meta_labeler_agent"):
    """Assign trade permission labels per ticker based on guardrail outputs."""
    data = state["data"]

    if not data.get("hybrid_mode", False):
        return {"messages": [], "data": {}}

    tickers = data["tickers"]
    guardrail_outputs = data.get("guardrail_outputs", {})
    debate_outputs = data.get("debate_outputs", {})
    meta_label_outputs: dict = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Applying meta-label rules")

        guardrail = guardrail_outputs.get(ticker, {})
        calibrated_confidence = int(guardrail.get("calibrated_confidence", 50))
        confidence_multiplier = float(guardrail.get("confidence_multiplier", 1.0))

        debate = debate_outputs.get(ticker)
        n_conflicts = len(debate.get("unresolved_conflicts", [])) if debate else 0

        # Priority: suppress > hold_only > reduce > allow (D-23)
        if calibrated_confidence < _SUPPRESS_CONFIDENCE or confidence_multiplier < _SUPPRESS_MULTIPLIER:
            label = "suppress"
            allow_trade = False
            size_multiplier = 0.0
        elif calibrated_confidence < _HOLD_ONLY_CONFIDENCE or confidence_multiplier < _HOLD_ONLY_MULTIPLIER:
            label = "hold_only"
            allow_trade = True
            size_multiplier = 0.5
        elif n_conflicts >= _REDUCE_CONFLICTS:
            label = "reduce"
            allow_trade = True
            size_multiplier = 0.7
        else:
            label = "allow"
            allow_trade = True
            size_multiplier = round(confidence_multiplier, 4)

        progress.update_status(agent_id, ticker, "Generating meta-label reasoning")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a trade admissibility analyst. Return a brief reasoning."),
            ("human", (
                "Ticker: {ticker}\nCalibrated confidence: {calibrated_confidence}\n"
                "Multiplier: {confidence_multiplier:.3f}\nUnresolved conflicts: {n_conflicts}\n"
                "Label: {label}\nAllow trade: {allow_trade}\nSize multiplier: {size_multiplier}\n\n"
                "In 2 sentences, justify this meta-label assignment."
            )),
        ])
        result = call_llm(
            prompt=prompt.format_messages(
                ticker=ticker, calibrated_confidence=calibrated_confidence,
                confidence_multiplier=confidence_multiplier, n_conflicts=n_conflicts,
                label=label, allow_trade=allow_trade, size_multiplier=size_multiplier,
            ),
            pydantic_model=_MetaReasoning, agent_name=agent_id, state=state,
        )

        meta_label_outputs[ticker] = MetaLabelOutput(
            ticker=ticker,
            allow_trade=allow_trade,
            size_multiplier=size_multiplier,
            label=label,
            reasoning=result.reasoning,
        ).model_dump()

        progress.update_status(agent_id, ticker, f"Label: {label} (size: {size_multiplier:.2f})")

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(meta_label_outputs, "Meta-Labeler Agent")

    message = HumanMessage(content=json.dumps(meta_label_outputs), name=agent_id)
    return {
        "messages": [message],
        "data": {"meta_label_outputs": meta_label_outputs},
    }
