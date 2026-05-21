import pytest
from pydantic import ValidationError

from src.data.models import (
    Price,
    PriceResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
)


class TestPrice:
    def test_valid_price(self):
        p = Price(open=100.0, close=101.0, high=102.0, low=99.0, volume=1000000, time="2024-03-01T05:00:00Z")
        assert p.open == 100.0
        assert p.time == "2024-03-01T05:00:00Z"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            Price(close=101.0, high=102.0, low=99.0, volume=1000000, time="2024-03-01")


def _make_full_metrics(**overrides) -> dict:
    """Build a complete FinancialMetrics kwargs dict with all nullable fields set to None."""
    from src.data.models import FinancialMetrics
    fields = FinancialMetrics.model_fields
    base = {"ticker": "AAPL", "report_period": "2024-03-31", "period": "ttm", "currency": "USD"}
    for name in fields:
        if name not in base:
            base[name] = None
    base.update(overrides)
    return base


class TestFinancialMetrics:
    def test_valid_metrics_all_nullable_none(self):
        m = FinancialMetrics(**_make_full_metrics())
        assert m.ticker == "AAPL"
        assert m.market_cap is None
        assert m.gross_margin is None

    def test_valid_metrics_with_values(self):
        m = FinancialMetrics(**_make_full_metrics(market_cap=3e12, gross_margin=0.70, return_on_equity=0.5))
        assert m.market_cap == 3e12
        assert m.gross_margin == 0.70

    def test_wrong_type_raises(self):
        with pytest.raises(ValidationError):
            FinancialMetrics(**_make_full_metrics(market_cap="not-a-number"))

    def test_missing_required_ticker_raises(self):
        kwargs = _make_full_metrics()
        del kwargs["ticker"]
        with pytest.raises(ValidationError):
            FinancialMetrics(**kwargs)


class TestLineItem:
    def test_valid_line_item_allows_extra_fields(self):
        li = LineItem(ticker="AAPL", report_period="2024-03-31", period="ttm", currency="USD", revenue=100e9)
        assert li.ticker == "AAPL"
        assert li.revenue == 100e9  # type: ignore[attr-defined]

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            LineItem(ticker="AAPL", period="ttm", currency="USD")


def _make_full_insider_trade(**overrides) -> dict:
    from src.data.models import InsiderTrade
    fields = InsiderTrade.model_fields
    base = {"ticker": "AAPL", "filing_date": "2024-01-15"}
    for name in fields:
        if name not in base:
            base[name] = None
    base.update(overrides)
    return base


class TestInsiderTrade:
    def test_valid_trade_with_optional_none(self):
        t = InsiderTrade(**_make_full_insider_trade())
        assert t.ticker == "AAPL"
        assert t.name is None
        assert t.transaction_value is None

    def test_valid_trade_with_values(self):
        t = InsiderTrade(
            ticker="AAPL",
            issuer="Apple Inc.",
            name="Tim Cook",
            title="CEO",
            is_board_director=False,
            transaction_date="2024-01-10",
            transaction_shares=1000.0,
            transaction_price_per_share=180.0,
            transaction_value=180000.0,
            shares_owned_before_transaction=5000.0,
            shares_owned_after_transaction=4000.0,
            security_title="Common Stock",
            filing_date="2024-01-15",
        )
        assert t.transaction_value == 180000.0

    def test_missing_filing_date_raises(self):
        kwargs = _make_full_insider_trade()
        del kwargs["filing_date"]
        with pytest.raises(ValidationError):
            InsiderTrade(**kwargs)


class TestPriceResponse:
    def test_valid_response(self):
        r = PriceResponse(
            ticker="AAPL",
            prices=[
                Price(open=100.0, close=101.0, high=102.0, low=99.0, volume=1000000, time="2024-03-01T05:00:00Z")
            ],
        )
        assert r.ticker == "AAPL"
        assert len(r.prices) == 1

    def test_empty_prices_list(self):
        r = PriceResponse(ticker="AAPL", prices=[])
        assert r.prices == []
