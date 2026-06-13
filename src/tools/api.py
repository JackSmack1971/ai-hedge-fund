import datetime
import logging
import os
import random
import threading
import time

import pandas as pd
import requests
from pydantic import ValidationError

_REQUEST_TIMEOUT = (10, 30)  # (connect_seconds, read_seconds)
_MAX_PAGINATION_PAGES = 100
_MAX_PAGINATION_SECONDS = 60.0
_BACKOFF_WAIT_EVENT = threading.Event()

from src.data.cache import get_cache
from src.data.models import (
    CompanyFactsResponse,
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    InsiderTrade,
    InsiderTradeResponse,
    LineItem,
    LineItemResponse,
    Price,
    PriceResponse,
)

# Global cache instance
_cache = get_cache()

logger = logging.getLogger(__name__)


def _response_snippet(response: requests.Response, limit: int = 200) -> str:
    try:
        return response.text[:limit]
    except Exception:
        return "<unreadable response body>"


def _log_http_error(endpoint: str, ticker: str, response: requests.Response) -> None:
    logger.error(
        "Error fetching %s for %s: HTTP %s — %s",
        endpoint,
        ticker,
        response.status_code,
        _response_snippet(response),
    )


def _log_parse_error(endpoint: str, ticker: str, exc: Exception, response: requests.Response) -> None:
    logger.error(
        "Failed to parse %s response for %s: %s — payload snippet: %s",
        endpoint,
        ticker,
        exc,
        _response_snippet(response),
    )


def _make_api_request(
    url: str, headers: dict, method: str = "GET", json_data: dict = None, max_retries: int = 3
) -> requests.Response:
    """
    Make an API request with rate limiting handling and moderate backoff.

    Args:
        url: The URL to request
        headers: Headers to include in the request
        method: HTTP method (GET or POST)
        json_data: JSON data for POST requests
        max_retries: Maximum number of retries (default: 3)

    Returns:
        requests.Response: The response object

    Raises:
        Exception: If the request fails with a non-429 error
    """
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=_REQUEST_TIMEOUT)
        else:
            response = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT)

        if response.status_code == 429 and attempt < max_retries:
            # Honour Retry-After header when present; otherwise full-jitter exponential backoff
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                delay = float(retry_after)
            else:
                cap = min(60.0, 1.0 * (2**attempt))
                delay = random.uniform(0, cap)
            logger.warning(
                "Rate limited (429). Attempt %s/%s. Retrying in %.1fs...", attempt + 1, max_retries + 1, delay
            )
            _BACKOFF_WAIT_EVENT.wait(timeout=delay)
            continue

        # Return the response (whether success, other errors, or final 429)
        return response


def _pagination_guard_hit(endpoint: str, ticker: str, page_count: int, session_started_at: float) -> bool:
    """Stop runaway pagination if the API keeps returning full pages or stalls."""
    if page_count >= _MAX_PAGINATION_PAGES:
        logger.warning(
            "Stopping %s pagination for %s after %s pages (max_pages=%s)",
            endpoint,
            ticker,
            page_count,
            _MAX_PAGINATION_PAGES,
        )
        return True

    elapsed = time.monotonic() - session_started_at
    if elapsed >= _MAX_PAGINATION_SECONDS:
        logger.warning(
            "Stopping %s pagination for %s after %.1fs (max_seconds=%.1f)",
            endpoint,
            ticker,
            elapsed,
            _MAX_PAGINATION_SECONDS,
        )
        return True

    return False


def get_prices(ticker: str, start_date: str, end_date: str, api_key: str = None) -> list[Price]:
    """Fetch price data from cache or API."""
    # Cache is keyed by ticker only so that a wide prefetch range covers all
    # narrow per-day queries in the backtest loop (fixes cache-key mismatch).
    if cached_data := _cache.get_prices(ticker):
        filtered = [p for p in cached_data if start_date <= p["time"][:10] <= end_date]
        if filtered:
            return [Price(**price) for price in filtered]

    # Range not in cache — fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    url = f"https://api.financialdatasets.ai/prices/?ticker={ticker}&interval=day&interval_multiplier=1&start_date={start_date}&end_date={end_date}"
    response = _make_api_request(url, headers)
    if response.status_code != 200:
        _log_http_error("prices", ticker, response)
        return []

    # Parse response with Pydantic model
    try:
        price_response = PriceResponse(**response.json())
        prices = price_response.prices
    except (ValidationError, ValueError, requests.RequestException) as e:
        _log_parse_error("prices", ticker, e, response)
        return []

    if not prices:
        return []

    # Store under ticker key; _cache.set_prices merges by 'time' to avoid duplicates
    _cache.set_prices(ticker, [p.model_dump() for p in prices])
    return prices


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str = None,
) -> list[FinancialMetrics]:
    """Fetch financial metrics from cache or API."""
    # Normalize to the maximum cache granularity used by current callers so
    # different per-agent limits collapse onto a single upstream fetch.
    cache_limit = max(limit, 12)
    cache_key = f"{ticker}_{period}_{end_date}_{cache_limit}"

    # Check cache first - exact match after normalization
    if cached_data := _cache.get_financial_metrics(cache_key):
        return [FinancialMetrics(**metric) for metric in cached_data][:limit]

    # If not in cache, fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    url = (
        "https://api.financialdatasets.ai/financial-metrics/"
        f"?ticker={ticker}&report_period_lte={end_date}&limit={cache_limit}&period={period}"
    )
    response = _make_api_request(url, headers)
    if response.status_code != 200:
        _log_http_error("financial metrics", ticker, response)
        return []

    # Parse response with Pydantic model
    try:
        metrics_response = FinancialMetricsResponse(**response.json())
        financial_metrics = metrics_response.financial_metrics
    except (ValidationError, ValueError, requests.RequestException) as e:
        _log_parse_error("financial metrics", ticker, e, response)
        return []

    if not financial_metrics:
        return []

    # Cache the results as dicts using the normalized cache key
    _cache.set_financial_metrics(cache_key, [m.model_dump() for m in financial_metrics])
    return financial_metrics[:limit]


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str = None,
) -> list[LineItem]:
    """Fetch line items from cache or API."""
    items_key = "_".join(sorted(line_items))
    cache_limit = max(limit, 12)
    cache_key = f"{ticker}_{period}_{end_date}_{cache_limit}_{items_key}"
    if cached_data := _cache.get_line_items(cache_key):
        return [LineItem(**item) for item in cached_data][:limit]

    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    url = "https://api.financialdatasets.ai/financials/search/line-items"

    body = {
        "tickers": [ticker],
        "line_items": line_items,
        "end_date": end_date,
        "period": period,
        "limit": cache_limit,
    }
    response = _make_api_request(url, headers, method="POST", json_data=body)
    if response.status_code != 200:
        _log_http_error("line items", ticker, response)
        return []

    try:
        data = response.json()
        response_model = LineItemResponse(**data)
        search_results = response_model.search_results
    except (ValidationError, ValueError, requests.RequestException) as e:
        _log_parse_error("line items", ticker, e, response)
        return []
    if not search_results:
        return []

    _cache.set_line_items(cache_key, [item.model_dump() for item in search_results])
    return search_results[:limit]


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str = None,
) -> list[InsiderTrade]:
    """Fetch insider trades from cache or API."""
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_insider_trades(cache_key):
        return [InsiderTrade(**trade) for trade in cached_data]

    # If not in cache, fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    all_trades = []
    current_end_date = end_date
    page_count = 0
    session_started_at = time.monotonic()

    while True:
        if _pagination_guard_hit("insider trades", ticker, page_count, session_started_at):
            break

        url = f"https://api.financialdatasets.ai/insider-trades/?ticker={ticker}&filing_date_lte={current_end_date}"
        if start_date:
            url += f"&filing_date_gte={start_date}"
        url += f"&limit={limit}"

        response = _make_api_request(url, headers)
        if response.status_code != 200:
            _log_http_error("insider trades", ticker, response)
            break

        try:
            data = response.json()
            response_model = InsiderTradeResponse(**data)
            insider_trades = response_model.insider_trades
        except (ValidationError, ValueError, requests.RequestException) as e:
            _log_parse_error("insider trades", ticker, e, response)
            break  # Parsing error, exit loop

        if not insider_trades:
            break

        all_trades.extend(insider_trades)
        page_count += 1

        # Only continue pagination if we have a start_date and got a full page
        if not start_date or len(insider_trades) < limit:
            break

        # Update end_date to the oldest filing date from current batch for next iteration
        current_end_date = min(trade.filing_date for trade in insider_trades).split("T")[0]

        # If we've reached or passed the start_date, we can stop
        if current_end_date <= start_date:
            break

    if not all_trades:
        return []

    # Cache the results using the comprehensive cache key
    _cache.set_insider_trades(cache_key, [trade.model_dump() for trade in all_trades])
    return all_trades


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str = None,
) -> list[CompanyNews]:
    """Fetch company news from cache or API."""
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_company_news(cache_key):
        return [CompanyNews(**news) for news in cached_data]

    # If not in cache, fetch from API
    headers = {}
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if financial_api_key:
        headers["X-API-KEY"] = financial_api_key

    all_news = []
    current_end_date = end_date
    page_count = 0
    session_started_at = time.monotonic()

    while True:
        if _pagination_guard_hit("company news", ticker, page_count, session_started_at):
            break

        url = f"https://api.financialdatasets.ai/news/?ticker={ticker}&end_date={current_end_date}"
        if start_date:
            url += f"&start_date={start_date}"
        url += f"&limit={limit}"

        response = _make_api_request(url, headers)
        if response.status_code != 200:
            _log_http_error("company news", ticker, response)
            break

        try:
            data = response.json()
            response_model = CompanyNewsResponse(**data)
            company_news = response_model.news
        except (ValidationError, ValueError, requests.RequestException) as e:
            _log_parse_error("company news", ticker, e, response)
            break  # Parsing error, exit loop

        if not company_news:
            break

        all_news.extend(company_news)
        page_count += 1

        # Only continue pagination if we have a start_date and got a full page
        if not start_date or len(company_news) < limit:
            break

        # Update end_date to the oldest date from current batch for next iteration
        current_end_date = min(news.date for news in company_news).split("T")[0]

        # If we've reached or passed the start_date, we can stop
        if current_end_date <= start_date:
            break

    if not all_news:
        return []

    # Cache the results using the comprehensive cache key
    _cache.set_company_news(cache_key, [news.model_dump() for news in all_news])
    return all_news


def get_market_cap(
    ticker: str,
    end_date: str,
    api_key: str = None,
) -> float | None:
    """Fetch market cap from the API."""
    # Check if end_date is today
    if end_date == datetime.datetime.now().strftime("%Y-%m-%d"):
        # Get the market cap from company facts API
        headers = {}
        financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
        if financial_api_key:
            headers["X-API-KEY"] = financial_api_key

        url = f"https://api.financialdatasets.ai/company/facts/?ticker={ticker}"
        response = _make_api_request(url, headers)
        if response.status_code != 200:
            _log_http_error("company facts", ticker, response)
            return None

        try:
            data = response.json()
            response_model = CompanyFactsResponse(**data)
            return response_model.company_facts.market_cap
        except (ValidationError, ValueError, requests.RequestException) as e:
            _log_parse_error("company facts", ticker, e, response)
            return None

    financial_metrics = get_financial_metrics(ticker, end_date, api_key=api_key)
    if not financial_metrics:
        return None

    market_cap = financial_metrics[0].market_cap

    if not market_cap:
        return None

    return market_cap


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str, api_key: str = None) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date, api_key=api_key)
    return prices_to_df(prices)
