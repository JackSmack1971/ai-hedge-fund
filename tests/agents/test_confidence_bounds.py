"""Regression tests for confidence range validation on agent output models."""

import pytest
from pydantic import ValidationError

from src.agents.charlie_munger import CharlieMungerSignal
from src.agents.news_sentiment import Sentiment
from src.agents.portfolio_manager import PortfolioDecision
from src.agents.warren_buffett import WarrenBuffettSignal


@pytest.mark.parametrize(
    ("model_cls", "kwargs"),
    [
        (Sentiment, {"sentiment": "positive", "confidence": 101}),
        (Sentiment, {"sentiment": "positive", "confidence": -1}),
        (CharlieMungerSignal, {"signal": "bullish", "confidence": 101, "reasoning": "x"}),
        (CharlieMungerSignal, {"signal": "bullish", "confidence": -1, "reasoning": "x"}),
        (WarrenBuffettSignal, {"signal": "bullish", "confidence": 101, "reasoning": "x"}),
        (WarrenBuffettSignal, {"signal": "bullish", "confidence": -1, "reasoning": "x"}),
        (PortfolioDecision, {"action": "hold", "quantity": 0, "confidence": 101, "reasoning": "x"}),
        (PortfolioDecision, {"action": "hold", "quantity": 0, "confidence": -1, "reasoning": "x"}),
        (PortfolioDecision, {"action": "hold", "quantity": -1, "confidence": 50, "reasoning": "x"}),
    ],
)
def test_confidence_bounds_enforced(model_cls, kwargs):
    with pytest.raises(ValidationError):
        model_cls(**kwargs)
