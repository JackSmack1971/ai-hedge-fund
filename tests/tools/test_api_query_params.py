from datetime import datetime
from unittest.mock import Mock, patch

from src.tools.api import (
    get_company_news,
    get_financial_metrics,
    get_insider_trades,
    get_market_cap,
    get_prices,
)


def _mock_response(payload):
    response = Mock()
    response.status_code = 200
    response.json.return_value = payload
    response.text = "ok"
    response.headers = {}
    return response


@patch("src.tools.api._cache")
@patch("src.tools.api.requests.get")
def test_get_prices_uses_query_params(mock_get, mock_cache):
    mock_cache.get_prices.return_value = None
    mock_get.return_value = _mock_response({"ticker": "AAPL&evil=1", "prices": []})

    result = get_prices("AAPL&evil=1", "2024-01-01", "2024-01-02")

    assert result == []
    assert mock_get.call_args.kwargs["params"] == {
        "ticker": "AAPL&evil=1",
        "interval": "day",
        "interval_multiplier": 1,
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
    }


@patch("src.tools.api._cache")
@patch("src.tools.api.requests.get")
def test_get_financial_metrics_uses_query_params(mock_get, mock_cache):
    mock_cache.get_financial_metrics.return_value = None
    mock_get.return_value = _mock_response({"financial_metrics": []})

    result = get_financial_metrics("AAPL&evil=1", "2024-01-02")

    assert result == []
    assert mock_get.call_args.kwargs["params"] == {
        "ticker": "AAPL&evil=1",
        "report_period_lte": "2024-01-02",
        "limit": 10,
        "period": "ttm",
    }


@patch("src.tools.api._cache")
@patch("src.tools.api.requests.get")
def test_get_insider_trades_uses_query_params(mock_get, mock_cache):
    mock_cache.get_insider_trades.return_value = None
    mock_get.return_value = _mock_response({"insider_trades": []})

    result = get_insider_trades("AAPL&evil=1", "2024-01-02")

    assert result == []
    assert mock_get.call_args.kwargs["params"] == {
        "ticker": "AAPL&evil=1",
        "filing_date_lte": "2024-01-02",
        "limit": 1000,
    }


@patch("src.tools.api._cache")
@patch("src.tools.api.requests.get")
def test_get_company_news_uses_query_params(mock_get, mock_cache):
    mock_cache.get_company_news.return_value = None
    mock_get.return_value = _mock_response({"news": []})

    result = get_company_news("AAPL&evil=1", "2024-01-02")

    assert result == []
    assert mock_get.call_args.kwargs["params"] == {
        "ticker": "AAPL&evil=1",
        "end_date": "2024-01-02",
        "limit": 1000,
    }


@patch("src.tools.api.requests.get")
def test_get_market_cap_uses_query_params(mock_get):
    today = datetime.now().strftime("%Y-%m-%d")
    mock_get.return_value = _mock_response(
        {
            "company_facts": {
                "ticker": "AAPL&evil=1",
                "name": "Apple Inc.",
            }
        }
    )

    result = get_market_cap("AAPL&evil=1", today)

    assert result is None
    assert mock_get.call_args.kwargs["params"] == {"ticker": "AAPL&evil=1"}
