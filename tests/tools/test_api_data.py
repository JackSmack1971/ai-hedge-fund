"""Tests for API data fetching functions in src/tools/api.py."""

import datetime
import json
from pathlib import Path
from unittest.mock import Mock, patch


from src.data.cache import Cache
from src.data.models import FinancialMetrics, Price
from src.tools.api import (
    _make_api_request,
    get_company_news,
    get_financial_metrics,
    get_insider_trades,
    get_market_cap,
    get_price_data,
    get_prices,
    prices_to_df,
)

FIXTURES = Path(__file__).parent.parent / "fixtures" / "api"


def load_fixture(rel_path: str) -> dict:
    with open(FIXTURES / rel_path) as f:
        return json.load(f)


def _mock_response(status_code: int, json_data) -> Mock:
    m = Mock()
    m.status_code = status_code
    m.json.return_value = json_data
    return m


def _financial_metric_payload(report_period: str) -> dict:
    """Build a complete FinancialMetrics payload row with nullable fields set to None."""
    base = {"ticker": "AAPL", "report_period": report_period, "period": "ttm", "currency": "USD"}
    for field_name in FinancialMetrics.model_fields:
        if field_name not in base:
            base[field_name] = None
    return base


class TestApiRetryBackoff:
    @patch("src.tools.api._BACKOFF_WAIT_EVENT.wait", return_value=False)
    @patch("src.tools.api.requests.get")
    def test_429_retry_uses_interruptible_event_wait(self, mock_get, mock_wait):
        first = _mock_response(429, {})
        first.headers = {"Retry-After": "2"}
        second = _mock_response(200, {})
        mock_get.side_effect = [first, second]

        response = _make_api_request("https://example.com", {})

        assert response.status_code == 200
        assert mock_get.call_count == 2
        mock_wait.assert_called_once_with(timeout=2.0)


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
            [
                {
                    "open": 179.0,
                    "close": 180.0,
                    "high": 181.0,
                    "low": 178.0,
                    "volume": 1000000,
                    "time": "2024-03-01T05:00:00Z",
                }
            ],
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

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_different_limits_produce_separate_api_calls(self, mock_cache, mock_request):
        payload = {
            "financial_metrics": [
                _financial_metric_payload(f"2024-{month:02d}-31") for month in range(1, 13)
            ]
        }
        mock_request.return_value = _mock_response(200, payload)

        result_5 = get_financial_metrics("AAPL", "2024-03-08", limit=5)
        result_8 = get_financial_metrics("AAPL", "2024-03-08", limit=8)
        result_12 = get_financial_metrics("AAPL", "2024-03-08", limit=12)

        assert mock_request.call_count == 3
        assert len(result_5) == 5
        assert len(result_8) == 8
        assert len(result_12) == 12

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_same_limit_reuses_cache(self, mock_cache, mock_request):
        payload = {
            "financial_metrics": [
                _financial_metric_payload(f"2024-{month:02d}-31") for month in range(1, 6)
            ]
        }
        mock_request.return_value = _mock_response(200, payload)

        result_a = get_financial_metrics("AAPL", "2024-03-08", limit=5)
        result_b = get_financial_metrics("AAPL", "2024-03-08", limit=5)

        assert mock_request.call_count == 1
        assert len(result_a) == 5
        assert len(result_b) == 5


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


# ──────────────────────────────────────────────────────────
# get_market_cap  (#200)
# ──────────────────────────────────────────────────────────

_COMPANY_FACTS_PAYLOAD = {
    "company_facts": {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "market_cap": 2_800_000_000_000.0,
    }
}


def _financial_metrics_payload(market_cap: float | None = 2_500_000_000_000.0) -> dict:
    """Build a valid FinancialMetricsResponse payload (all nullable fields present)."""
    base = load_fixture("financial_metrics/AAPL_2024-03-01_2024-03-08.json")
    base["financial_metrics"][0]["market_cap"] = market_cap
    return base


class TestGetMarketCap:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_today_branch_returns_company_facts_cap(self, mock_cache, mock_request):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        mock_request.return_value = _mock_response(200, _COMPANY_FACTS_PAYLOAD)
        result = get_market_cap("AAPL", today)
        assert result == 2_800_000_000_000.0

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_today_branch_non_200_returns_none(self, mock_cache, mock_request):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        mock_request.return_value = _mock_response(404, {})
        result = get_market_cap("AAPL", today)
        assert result is None

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_historical_branch_returns_metrics_cap(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, _financial_metrics_payload(2_500_000_000_000.0))
        result = get_market_cap("AAPL", "2024-03-08")
        assert result == 2_500_000_000_000.0

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_historical_branch_empty_metrics_returns_none(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, {"financial_metrics": []})
        result = get_market_cap("AAPL", "2024-03-08")
        assert result is None

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_historical_branch_null_cap_returns_none(self, mock_cache, mock_request):
        mock_request.return_value = _mock_response(200, _financial_metrics_payload(None))
        result = get_market_cap("AAPL", "2024-03-08")
        assert result is None


# ──────────────────────────────────────────────────────────
# prices_to_df / get_price_data  (#200)
# ──────────────────────────────────────────────────────────


def _make_price(time: str = "2024-03-01T05:00:00Z", close: float = 180.0) -> Price:
    return Price(open=179.0, close=close, high=181.0, low=178.0, volume=1_000_000, time=time)


class TestPricesToDf:
    def test_valid_prices_produces_datetime_index(self):
        prices = [_make_price("2024-03-01T05:00:00Z"), _make_price("2024-03-04T05:00:00Z")]
        df = prices_to_df(prices)
        import pandas as pd

        assert isinstance(df.index, pd.DatetimeIndex)

    def test_numeric_close_column(self):
        df = prices_to_df([_make_price(close=123.45)])
        assert df["close"].dtype.kind == "f"

    def test_out_of_order_dates_sorted_ascending(self):
        prices = [
            _make_price("2024-03-04T05:00:00Z", close=182.0),
            _make_price("2024-03-01T05:00:00Z", close=179.0),
        ]
        df = prices_to_df(prices)
        assert df["close"].iloc[0] == 179.0
        assert df["close"].iloc[1] == 182.0

    def test_single_price_returns_one_row(self):
        df = prices_to_df([_make_price()])
        assert len(df) == 1


class TestGetPriceData:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_returns_dataframe_with_close(self, mock_cache, mock_request):
        payload = load_fixture("prices/AAPL_2024-03-01_2024-03-08.json")
        mock_request.return_value = _mock_response(200, payload)
        df = get_price_data("AAPL", "2024-03-01", "2024-03-08")
        assert not df.empty
        assert "close" in df.columns


# ──────────────────────────────────────────────────────────
# Pagination tests for get_insider_trades / get_company_news  (#202)
# ──────────────────────────────────────────────────────────


def _trade(filing_date: str) -> dict:
    return {
        "ticker": "AAPL",
        "issuer": None,
        "name": None,
        "title": None,
        "is_board_director": None,
        "transaction_date": None,
        "transaction_shares": 100,
        "transaction_price_per_share": 150.0,
        "transaction_value": 15000.0,
        "shares_owned_before_transaction": 1000,
        "shares_owned_after_transaction": 1100,
        "security_title": None,
        "filing_date": filing_date,
    }


def _news(date: str) -> dict:
    return {
        "ticker": "AAPL",
        "title": "News item",
        "author": "Reporter",
        "source": "Reuters",
        "date": date,
        "url": "https://reuters.com/a",
    }


class TestInsiderTradesPagination:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_two_pages_combined(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"insider_trades": [_trade("2024-03-05"), _trade("2024-02-10")]})
        page2 = _mock_response(200, {"insider_trades": [_trade("2024-01-20")]})
        mock_request.side_effect = [page1, page2]
        result = get_insider_trades("AAPL", "2024-03-08", start_date="2024-01-01", limit=2)
        assert len(result) == 3
        assert mock_request.call_count == 2

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_partial_page_stops_after_one_call(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"insider_trades": [_trade("2024-03-05")]})
        mock_request.return_value = page1
        result = get_insider_trades("AAPL", "2024-03-08", start_date="2024-01-01", limit=5)
        assert len(result) == 1
        assert mock_request.call_count == 1

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_no_start_date_single_call(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"insider_trades": [_trade("2024-03-05"), _trade("2024-02-10")]})
        mock_request.return_value = page1
        result = get_insider_trades("AAPL", "2024-03-08", limit=2)
        assert len(result) == 2
        assert mock_request.call_count == 1

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_iso_timestamp_filing_date_split(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"insider_trades": [_trade("2024-03-05T14:30:00Z"), _trade("2024-02-10T00:00:00")]})
        page2 = _mock_response(200, {"insider_trades": [_trade("2024-01-20")]})
        mock_request.side_effect = [page1, page2]
        result = get_insider_trades("AAPL", "2024-03-08", start_date="2024-01-01", limit=2)
        assert len(result) == 3

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_end_date_reached_stops_loop(self, mock_cache, mock_request):
        # oldest filing_date on page1 is already <= start_date → stop after page1
        page1 = _mock_response(200, {"insider_trades": [_trade("2024-01-15"), _trade("2024-01-01")]})
        mock_request.return_value = page1
        result = get_insider_trades("AAPL", "2024-03-08", start_date="2024-01-10", limit=2)
        assert len(result) == 2
        assert mock_request.call_count == 1

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_page2_error_returns_page1_results(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"insider_trades": [_trade("2024-03-05"), _trade("2024-02-10")]})
        page2 = _mock_response(500, {})
        mock_request.side_effect = [page1, page2]
        result = get_insider_trades("AAPL", "2024-03-08", start_date="2024-01-01", limit=2)
        assert len(result) == 2


class TestCompanyNewsPagination:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_two_pages_combined(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"news": [_news("2024-03-05"), _news("2024-02-10")]})
        page2 = _mock_response(200, {"news": [_news("2024-01-20")]})
        mock_request.side_effect = [page1, page2]
        result = get_company_news("AAPL", "2024-03-08", start_date="2024-01-01", limit=2)
        assert len(result) == 3
        assert mock_request.call_count == 2

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_partial_page_stops_after_one_call(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"news": [_news("2024-03-05")]})
        mock_request.return_value = page1
        result = get_company_news("AAPL", "2024-03-08", start_date="2024-01-01", limit=5)
        assert len(result) == 1
        assert mock_request.call_count == 1

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_no_start_date_single_call(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"news": [_news("2024-03-05"), _news("2024-02-10")]})
        mock_request.return_value = page1
        result = get_company_news("AAPL", "2024-03-08", limit=2)
        assert len(result) == 2
        assert mock_request.call_count == 1

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_end_date_reached_stops_loop(self, mock_cache, mock_request):
        page1 = _mock_response(200, {"news": [_news("2024-01-15"), _news("2024-01-01")]})
        mock_request.return_value = page1
        result = get_company_news("AAPL", "2024-03-08", start_date="2024-01-10", limit=2)
        assert len(result) == 2
        assert mock_request.call_count == 1


class TestPaginationGuards:
    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_insider_trades_max_pages_guard(self, mock_cache, mock_request, caplog):
        page = _mock_response(200, {"insider_trades": [_trade("2024-03-05"), _trade("2024-02-10")]})
        mock_request.return_value = page

        with caplog.at_level("WARNING"):
            result = get_insider_trades("AAPL", "2024-03-08", start_date="2024-01-01", limit=2)

        assert len(result) == 200
        assert mock_request.call_count == 100
        assert "max_pages=100" in caplog.text

    @patch("src.tools.api._make_api_request")
    @patch("src.tools.api._cache", new_callable=Cache)
    def test_company_news_max_pages_guard(self, mock_cache, mock_request, caplog):
        page = _mock_response(200, {"news": [_news("2024-03-05"), _news("2024-02-10")]})
        mock_request.return_value = page

        with caplog.at_level("WARNING"):
            result = get_company_news("AAPL", "2024-03-08", start_date="2024-01-01", limit=2)

        assert len(result) == 200
        assert mock_request.call_count == 100
        assert "max_pages=100" in caplog.text
