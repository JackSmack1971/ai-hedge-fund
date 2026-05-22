import pytest

from src.backtesting.portfolio import Portfolio
from src.backtesting.trader import TradeExecutor


def test_trade_executor_routes_actions(portfolio):
    ex = TradeExecutor()

    # buy
    qty = ex.execute_trade("AAPL", "buy", 10, 100.0, portfolio)
    assert qty == 10
    # sell
    qty = ex.execute_trade("AAPL", "sell", 5, 100.0, portfolio)
    assert qty == 5
    # short
    qty = ex.execute_trade("MSFT", "short", 4, 200.0, portfolio)
    assert qty == 4
    # cover
    qty = ex.execute_trade("MSFT", "cover", 1, 200.0, portfolio)
    assert qty == 1


def test_trade_executor_guards_and_unknown_action(portfolio):
    ex = TradeExecutor()

    assert ex.execute_trade("AAPL", "buy", 0, 10.0, portfolio) == 0
    assert ex.execute_trade("AAPL", "buy", -5, 10.0, portfolio) == 0
    assert ex.execute_trade("AAPL", "unknown", 10, 10.0, portfolio) == 0


# ──────────────────────────────────────────────────────────
# Portfolio financial state assertions (#213)
# ──────────────────────────────────────────────────────────


def _fresh_portfolio() -> Portfolio:
    return Portfolio(tickers=["AAPL", "MSFT"], initial_cash=100_000.0, margin_requirement=0.5)


def test_buy_reduces_cash_and_increases_long_position():
    p = _fresh_portfolio()
    ex = TradeExecutor()
    qty = ex.execute_trade("AAPL", "buy", 100, 150.0, p)
    assert qty == 100
    assert p.get_cash() == pytest.approx(100_000.0 - 100 * 150.0)
    assert p.get_positions()["AAPL"]["long"] == 100
    assert p.get_positions()["AAPL"]["long_cost_basis"] == pytest.approx(150.0)


def test_sell_increases_cash_and_records_gain():
    p = _fresh_portfolio()
    ex = TradeExecutor()
    ex.execute_trade("AAPL", "buy", 100, 100.0, p)
    cash_after_buy = p.get_cash()
    ex.execute_trade("AAPL", "sell", 100, 120.0, p)
    assert p.get_cash() == pytest.approx(cash_after_buy + 100 * 120.0)
    assert p.get_positions()["AAPL"]["long"] == 0
    assert p.get_realized_gains()["AAPL"]["long"] == pytest.approx(100 * (120.0 - 100.0))


def test_sell_records_loss():
    p = _fresh_portfolio()
    ex = TradeExecutor()
    ex.execute_trade("AAPL", "buy", 100, 150.0, p)
    ex.execute_trade("AAPL", "sell", 100, 120.0, p)
    assert p.get_realized_gains()["AAPL"]["long"] == pytest.approx(100 * (120.0 - 150.0))


def test_short_increases_cash_by_net_proceeds_and_uses_margin():
    p = _fresh_portfolio()
    ex = TradeExecutor()
    initial_cash = p.get_cash()
    qty = ex.execute_trade("MSFT", "short", 100, 200.0, p)
    assert qty == 100
    proceeds = 100 * 200.0
    margin = proceeds * 0.5
    assert p.get_cash() == pytest.approx(initial_cash + proceeds - margin)
    assert p.get_margin_used() == pytest.approx(margin)
    assert p.get_positions()["MSFT"]["short"] == 100


def test_cover_releases_margin_and_records_gain():
    p = _fresh_portfolio()
    ex = TradeExecutor()
    ex.execute_trade("MSFT", "short", 100, 200.0, p)
    cash_after_short = p.get_cash()
    margin_after_short = p.get_margin_used()
    qty = ex.execute_trade("MSFT", "cover", 100, 150.0, p)
    assert qty == 100
    assert p.get_margin_used() == pytest.approx(0.0, abs=1e-9)
    assert p.get_positions()["MSFT"]["short"] == 0
    assert p.get_realized_gains()["MSFT"]["short"] == pytest.approx(100 * (200.0 - 150.0))


def test_zero_quantity_leaves_portfolio_unchanged():
    p = _fresh_portfolio()
    ex = TradeExecutor()
    snap_before = p.get_snapshot()
    qty = ex.execute_trade("AAPL", "buy", 0, 100.0, p)
    assert qty == 0
    snap_after = p.get_snapshot()
    assert snap_after["cash"] == snap_before["cash"]
    assert snap_after["margin_used"] == snap_before["margin_used"]


def test_insufficient_cash_executes_partial():
    p = Portfolio(tickers=["AAPL"], initial_cash=500.0, margin_requirement=0.5)
    ex = TradeExecutor()
    qty = ex.execute_trade("AAPL", "buy", 100, 150.0, p)
    assert qty < 100
    assert p.get_cash() < 500.0

