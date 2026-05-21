"""Shared fixtures and helpers for agent tests."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any

import pytest
from langchain_core.messages import AIMessage

FIXTURES = Path(__file__).parent.parent / "fixtures" / "api"


def load_fixture(rel_path: str) -> dict:
    with open(FIXTURES / rel_path) as f:
        return json.load(f)


def _make_bullish_llm_response(model_class) -> Any:
    """Return a mock LLM result with bullish signal."""
    instance = model_class(signal="bullish", confidence=75, reasoning="Strong fundamentals")
    return instance


def _make_neutral_llm_response(model_class) -> Any:
    instance = model_class(signal="neutral", confidence=50, reasoning="Mixed signals")
    return instance


def _make_mock_prices():
    fixture = load_fixture("prices/AAPL_2024-03-01_2024-03-08.json")
    from src.data.models import Price
    return [Price(**p) for p in fixture["prices"]]


def _make_mock_financial_metrics():
    fixture = load_fixture("financial_metrics/AAPL_2024-03-01_2024-03-08.json")
    from src.data.models import FinancialMetrics
    return [FinancialMetrics(**m) for m in fixture["financial_metrics"]]


def _make_mock_insider_trades():
    fixture = load_fixture("insider_trades/AAPL_2024-03-01_2024-03-08.json")
    from src.data.models import InsiderTrade
    return [InsiderTrade(**t) for t in fixture["insider_trades"]]


def _make_empty_state(tickers=None, ticker="AAPL") -> dict:
    """Build a minimal AgentState dict for testing."""
    if tickers is None:
        tickers = [ticker]
    return {
        "messages": [],
        "data": {
            "tickers": tickers,
            "start_date": "2024-03-01",
            "end_date": "2024-03-08",
            "analyst_signals": {},
            "portfolio": {
                "cash": 100000.0,
                "positions": {t: {"long": 0, "short": 0} for t in tickers},
                "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in tickers},
            },
        },
        "metadata": {
            "model_name": "gpt-4o",
            "model_provider": "OpenAI",
            "show_reasoning": False,
        },
    }


@pytest.fixture
def mock_api_calls():
    """Patch all external API calls used by agents."""
    prices = _make_mock_prices()
    metrics = _make_mock_financial_metrics()
    trades = _make_mock_insider_trades()

    with (
        patch("src.tools.api.get_prices", return_value=prices),
        patch("src.tools.api.get_financial_metrics", return_value=metrics),
        patch("src.tools.api.get_insider_trades", return_value=trades),
        patch("src.tools.api.get_company_news", return_value=[]),
        patch("src.tools.api.get_market_cap", return_value=3e12),
        patch("src.tools.api.search_line_items", return_value=[]),
        patch("src.tools.api.get_price_data", return_value=__import__("pandas").DataFrame()),
    ):
        yield


@pytest.fixture
def mock_llm():
    """Patch call_llm to return a controlled bullish response."""
    def _fake_call_llm(prompt, pydantic_model, agent_name=None, state=None, max_retries=3, default_factory=None):
        return _make_bullish_llm_response(pydantic_model)

    with patch("src.utils.llm.call_llm", side_effect=_fake_call_llm):
        with patch("src.agents.warren_buffett.call_llm", side_effect=_fake_call_llm):
            with patch("src.agents.charlie_munger.call_llm", side_effect=_fake_call_llm):
                with patch("src.agents.ben_graham.call_llm", side_effect=_fake_call_llm):
                    with patch("src.agents.cathie_wood.call_llm", side_effect=_fake_call_llm):
                        with patch("src.agents.bill_ackman.call_llm", side_effect=_fake_call_llm):
                            with patch("src.agents.technicals.call_llm", side_effect=_fake_call_llm):
                                with patch("src.agents.sentiment.call_llm", side_effect=_fake_call_llm):
                                    with patch("src.agents.fundamentals.call_llm", side_effect=_fake_call_llm):
                                        with patch("src.agents.valuation.call_llm", side_effect=_fake_call_llm):
                                            yield _fake_call_llm


@pytest.fixture
def agent_state():
    return _make_empty_state()


@pytest.fixture
def empty_data_state():
    """State with no API data — tests graceful degradation."""
    return _make_empty_state()
