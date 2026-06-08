from src.backtesting.controller import AgentController


def dummy_agent(**kwargs):
    tickers = kwargs["tickers"]
    return {
        "decisions": {tickers[0]: {"action": "buy", "quantity": "10"}},
        "analyst_signals": {"agentA": {tickers[0]: {"signal": "bullish"}}},
    }


def test_agent_controller_normalizes_and_snapshots(portfolio):
    ctrl = AgentController()
    out = ctrl.run_agent(
        dummy_agent,
        tickers=["AAPL", "MSFT"],
        start_date="2024-01-01",
        end_date="2024-01-10",
        portfolio=portfolio,
        model_name="m",
        model_provider="p",
        selected_analysts=["x"],
    )

    assert out["decisions"]["AAPL"]["action"] == "buy"
    assert out["decisions"]["AAPL"]["quantity"] == 10.0
    assert out["decisions"]["MSFT"]["action"] == "hold"
    assert out["decisions"]["MSFT"]["quantity"] == 0.0
    assert "agentA" in out["analyst_signals"]


def test_conflicting_signals_both_normalized(portfolio):
    """Two agents give conflicting signals — controller normalizes both independently."""

    def conflicting_agent(**kwargs):
        tickers = kwargs["tickers"]
        return {
            "decisions": {
                tickers[0]: {"action": "buy", "quantity": 5},
                tickers[1]: {"action": "sell", "quantity": 10},
            },
            "analyst_signals": {
                "bullAgent": {tickers[0]: {"signal": "bullish"}},
                "bearAgent": {tickers[1]: {"signal": "bearish"}},
            },
        }

    ctrl = AgentController()
    out = ctrl.run_agent(
        conflicting_agent,
        tickers=["AAPL", "MSFT"],
        start_date="2024-01-01",
        end_date="2024-01-10",
        portfolio=portfolio,
        model_name="m",
        model_provider="p",
        selected_analysts=["x"],
    )
    assert out["decisions"]["AAPL"]["action"] == "buy"
    assert out["decisions"]["MSFT"]["action"] == "sell"
    assert "bullAgent" in out["analyst_signals"]
    assert "bearAgent" in out["analyst_signals"]


def test_invalid_signal_falls_back_to_hold(portfolio):
    """Agent returns an invalid action string — controller coerces to hold."""

    def bad_action_agent(**kwargs):
        tickers = kwargs["tickers"]
        return {
            "decisions": {tickers[0]: {"action": "rocket_to_moon", "quantity": 100}},
            "analyst_signals": {},
        }

    ctrl = AgentController()
    out = ctrl.run_agent(
        bad_action_agent,
        tickers=["AAPL"],
        start_date="2024-01-01",
        end_date="2024-01-10",
        portfolio=portfolio,
        model_name="m",
        model_provider="p",
        selected_analysts=["x"],
    )
    assert out["decisions"]["AAPL"]["action"] == "hold"


def test_all_neutral_signals(portfolio):
    """Agent returns only hold for all tickers."""

    def neutral_agent(**kwargs):
        tickers = kwargs["tickers"]
        return {
            "decisions": {t: {"action": "hold", "quantity": 0} for t in tickers},
            "analyst_signals": {},
        }

    ctrl = AgentController()
    out = ctrl.run_agent(
        neutral_agent,
        tickers=["AAPL", "MSFT", "TSLA"],
        start_date="2024-01-01",
        end_date="2024-01-10",
        portfolio=portfolio,
        model_name="m",
        model_provider="p",
        selected_analysts=["x"],
    )
    for ticker in ["AAPL", "MSFT", "TSLA"]:
        assert out["decisions"][ticker]["action"] == "hold"
        assert out["decisions"][ticker]["quantity"] == 0.0
