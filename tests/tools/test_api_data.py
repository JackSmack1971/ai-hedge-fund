"""Tests for API data fetching functions in src/tools/api.py."""
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.tools.api import (
    get_prices,
    get_financial_metrics,
    get_company_news,
    get_insider_trades,
    get_market_cap,
)
from src.data.cache import Cache

FIXTURES = Path(__file__).parent.parent / "fixtures" / "api"


def load_fixture(rel_path: str) -> dict:
    with open(FIXTURES / rel_path) as f:
        return json.load(f)


def _mock_response(status_code: int, json_data) -> Mock:
    m = Mock()
    m.status_code = status_code
    m.json.return_value = json_data
    return m


# ──────────────────────────────────────────────────────────
# get_prices
# ──────────────────────────────────────────────────────────

class TestGetPrices:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_happy_path(self, mock_cache, mock_request):
        payload = load_fixture("prices/AAPL_2024-03-01_2024-03-08.json")
        mock_request.return_value = _mock_response(200, payload)
        result = get_prices("AAPL", "2024-03-01", "2024-03-08")
        assert len(result) > 0
        assert result[0].open > 0
        assert result[0].time is not None

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_empty_response(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"ticker": "AAPL", "prices": []})
        result = get_prices("AAPL", "2024-03-01", "2024-03-08")
        assert result == []

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_non_200_response_returns_empty(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(500, {})
        result = get_prices("AAPL", "2024-03-01", "2024-03-08")
        assert result == []

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_malformed_response_returns_empty(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"unexpected": "structure"})
        result = get_prices("AAPL", "2024-03-01", "2024-03-08")
        assert result == []

    def test_cache_hit_skips_http(self):
        fresh_cache = Cache()
        # Cache is keyed by ticker only; the range filter happens inside get_prices()
        fresh_cache.set_prices(
            "AAPL",
            [{"open": 179.0, "close": 180.0, "high": 181.0, "low": 178.0, "volume": 1000000, "time": "2024-03-01T05:00:00Z"}],
        )
        with patch("src.tools.api._cache", fresh_cache):
            with patch("src.tools.api._make_api_request") as mock_req:
                result = get_prices("AAPL", "2024-03-01", "2024-03-08")
                mock_req.assert_not_called()
                assert len(result) == 1


# ──────────────────────────────────────────────────────────
# get_financial_metrics
# ──────────────────────────────────────────────────────────

class TestGetFinancialMetrics:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_happy_path(self, mock_cache, mock_request):
        payload = load_fixture("financial_metrics/AAPL_2024-03-01_2024-03-08.json")
        mock_request.return_value = _mock_response(200, payload)
        result = get_financial_metrics("AAPL", "2024-03-08")
        assert len(result) > 0
        assert result[0].ticker == "AAPL"
        assert result[0].report_period is not None

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_empty_response(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"financial_metrics": []})
        result = get_financial_metrics("AAPL", "2024-03-08")
        assert result == []

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_non_200_returns_empty(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(403, {})
        result = get_financial_metrics("AAPL", "2024-03-08")
        assert result == []

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_malformed_response_returns_empty(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"bad": "data"})
        result = get_financial_metrics("AAPL", "2024-03-08")
        assert result == []


# ──────────────────────────────────────────────────────────
# get_company_news
# ──────────────────────────────────────────────────────────

class TestGetCompanyNews:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_happy_path(self, mock_cache, mock_request):
        payload = load_fixture("news/AAPL_2024-03-01_2024-03-08.json")
        # The API returns {"news": [...]} but our model uses CompanyNewsResponse
        mock_request.return_value = _mock_response(200, payload)
        result = get_company_news("AAPL", "2024-03-08")
        assert isinstance(result, list)

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_empty_response(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"news": []})
        result = get_company_news("AAPL", "2024-03-08")
        assert result == []

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_non_200_returns_empty(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(404, {})
        result = get_company_news("AAPL", "2024-03-08")
        assert result == []

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_malformed_response_returns_empty(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"garbage": True})
        result = get_company_news("AAPL", "2024-03-08")
        assert result == []


# ──────────────────────────────────────────────────────────
# get_insider_trades
# ──────────────────────────────────────────────────────────

class TestGetInsiderTrades:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_happy_path(self, mock_cache, mock_request):
        payload = load_fixture("insider_trades/AAPL_2024-03-01_2024-03-08.json")
        mock_request.return_value = _mock_response(200, payload)
        result = get_insider_trades("AAPL", "2024-03-08")
        assert isinstance(result, list)

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_empty_response(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"insider_trades": []})
        result = get_insider_trades("AAPL", "2024-03-08")
        assert result == []

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_non_200_returns_empty(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(401, {})
        result = get_insider_trades("AAPL", "2024-03-08")
        assert result == []

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_malformed_response_returns_empty(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"wrong": "schema"})
        result = get_insider_trades("AAPL", "2024-03-08")
        assert result == []
