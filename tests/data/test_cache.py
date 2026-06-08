import pytest

from src.data.cache import Cache


@pytest.fixture
def cache():
    return Cache()


# --- Prices ---


def test_prices_miss_returns_none(cache):
    assert cache.get_prices("AAPL") is None


def test_prices_set_and_get(cache):
    data = [{"time": "2024-01-01", "open": 100.0, "close": 101.0}]
    cache.set_prices("AAPL", data)
    result = cache.get_prices("AAPL")
    assert result == data


def test_prices_merge_non_overlapping(cache):
    a = [{"time": "2024-01-01", "close": 100.0}]
    b = [{"time": "2024-01-02", "close": 101.0}]
    cache.set_prices("AAPL", a)
    cache.set_prices("AAPL", b)
    result = cache.get_prices("AAPL")
    times = {r["time"] for r in result}
    assert "2024-01-01" in times
    assert "2024-01-02" in times
    assert len(result) == 2


def test_prices_merge_deduplicates(cache):
    a = [{"time": "2024-01-01", "close": 100.0}]
    b = [{"time": "2024-01-01", "close": 100.0}, {"time": "2024-01-02", "close": 101.0}]
    cache.set_prices("AAPL", a)
    cache.set_prices("AAPL", b)
    result = cache.get_prices("AAPL")
    assert len(result) == 2


def test_prices_merge_empty_new_data(cache):
    a = [{"time": "2024-01-01", "close": 100.0}]
    cache.set_prices("AAPL", a)
    cache.set_prices("AAPL", [])
    result = cache.get_prices("AAPL")
    assert len(result) == 1


def test_prices_merge_with_empty_existing(cache):
    b = [{"time": "2024-01-01", "close": 100.0}]
    cache.set_prices("AAPL", b)
    result = cache.get_prices("AAPL")
    assert len(result) == 1


def test_prices_different_tickers_isolated(cache):
    cache.set_prices("AAPL", [{"time": "2024-01-01", "close": 100.0}])
    cache.set_prices("MSFT", [{"time": "2024-01-01", "close": 200.0}])
    aapl = cache.get_prices("AAPL")
    msft = cache.get_prices("MSFT")
    assert aapl[0]["close"] == 100.0
    assert msft[0]["close"] == 200.0


# --- Financial Metrics ---


def test_financial_metrics_miss_returns_none(cache):
    assert cache.get_financial_metrics("AAPL") is None


def test_financial_metrics_set_and_get(cache):
    data = [{"report_period": "2024-03-31", "market_cap": 1e12}]
    cache.set_financial_metrics("AAPL", data)
    result = cache.get_financial_metrics("AAPL")
    assert result == data


def test_financial_metrics_deduplication(cache):
    a = [{"report_period": "2024-03-31", "market_cap": 1e12}]
    b = [{"report_period": "2024-03-31", "market_cap": 1e12}, {"report_period": "2023-12-31", "market_cap": 0.9e12}]
    cache.set_financial_metrics("AAPL", a)
    cache.set_financial_metrics("AAPL", b)
    result = cache.get_financial_metrics("AAPL")
    assert len(result) == 2


# --- Insider Trades ---


def test_insider_trades_miss_returns_none(cache):
    assert cache.get_insider_trades("AAPL") is None


def test_insider_trades_set_and_get(cache):
    data = [{"filing_date": "2024-01-15", "transaction_value": 50000.0}]
    cache.set_insider_trades("AAPL", data)
    result = cache.get_insider_trades("AAPL")
    assert result == data


def test_insider_trades_merge_deduplicates_by_filing_date(cache):
    a = [{"filing_date": "2024-01-15", "transaction_value": 50000.0}]
    b = [
        {"filing_date": "2024-01-15", "transaction_value": 50000.0},
        {"filing_date": "2024-02-01", "transaction_value": 10000.0},
    ]
    cache.set_insider_trades("AAPL", a)
    cache.set_insider_trades("AAPL", b)
    result = cache.get_insider_trades("AAPL")
    assert len(result) == 2


# --- Company News ---


def test_company_news_miss_returns_none(cache):
    assert cache.get_company_news("AAPL") is None


def test_company_news_set_and_get(cache):
    data = [{"date": "2024-03-01", "title": "Apple announces new product"}]
    cache.set_company_news("AAPL", data)
    result = cache.get_company_news("AAPL")
    assert result == data


def test_company_news_merge_non_overlapping(cache):
    a = [{"date": "2024-03-01", "title": "News A"}]
    b = [{"date": "2024-03-02", "title": "News B"}]
    cache.set_company_news("AAPL", a)
    cache.set_company_news("AAPL", b)
    result = cache.get_company_news("AAPL")
    assert len(result) == 2


def test_company_news_deduplication(cache):
    a = [{"date": "2024-03-01", "title": "News A"}]
    cache.set_company_news("AAPL", a)
    cache.set_company_news("AAPL", a)
    result = cache.get_company_news("AAPL")
    assert len(result) == 1


# --- Line Items ---


def test_line_items_miss_returns_none(cache):
    assert cache.get_line_items("AAPL") is None


def test_line_items_set_and_get(cache):
    data = [{"report_period": "2024-03-31", "revenue": 100e9}]
    cache.set_line_items("AAPL", data)
    result = cache.get_line_items("AAPL")
    assert result == data


# --- Merge helper ---


def test_merge_empty_existing_returns_new_data(cache):
    new_data = [{"time": "2024-01-01", "close": 100.0}]
    result = cache._merge_data(None, new_data, "time")
    assert result == new_data


def test_merge_fully_overlapping_returns_existing(cache):
    existing = [{"time": "2024-01-01", "close": 100.0}]
    new_data = [{"time": "2024-01-01", "close": 100.0}]
    result = cache._merge_data(existing, new_data, "time")
    assert len(result) == 1


def test_merge_single_record_dataset(cache):
    existing = [{"time": "2024-01-01", "close": 100.0}]
    new_data = [{"time": "2024-01-02", "close": 101.0}]
    result = cache._merge_data(existing, new_data, "time")
    assert len(result) == 2
