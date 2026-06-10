"""ROUT-02 tests: adaptive analyst selector based on market regime."""

import pytest

from src.regime.selector import select_analysts_for_regime


_ALL_ANALYSTS = [
    "warren_buffett", "charlie_munger", "ben_graham", "cathie_wood", "bill_ackman",
    "technicals", "fundamentals", "valuation", "sentiment", "news_sentiment",
    "stanley_druckenmiller", "peter_lynch", "aswath_damodaran",
]


class TestSelectAnalystsForRegime:
    def test_unknown_regime_returns_all(self):
        result = select_analysts_for_regime("unknown", _ALL_ANALYSTS)
        assert set(result) == set(_ALL_ANALYSTS)

    def test_risk_on_returns_all(self):
        result = select_analysts_for_regime("risk_on", _ALL_ANALYSTS)
        assert set(result) == set(_ALL_ANALYSTS)

    def test_high_volatility_prefers_technicals(self):
        result = select_analysts_for_regime("high_volatility", _ALL_ANALYSTS)
        assert "technicals" in result

    def test_low_volatility_prefers_value_analysts(self):
        result = select_analysts_for_regime("low_volatility", _ALL_ANALYSTS)
        assert "warren_buffett" in result or "ben_graham" in result

    def test_momentum_prefers_technicals_and_cathie(self):
        result = select_analysts_for_regime("momentum", _ALL_ANALYSTS)
        assert "technicals" in result or "cathie_wood" in result

    def test_risk_off_prefers_value(self):
        result = select_analysts_for_regime("risk_off", _ALL_ANALYSTS)
        assert "warren_buffett" in result or "ben_graham" in result

    def test_min_analysts_respected(self):
        """Even a narrow regime must return at least min_analysts."""
        small_set = ["technicals"]
        result = select_analysts_for_regime("risk_off", small_set, min_analysts=1)
        assert len(result) >= 1

    def test_fallback_when_no_preferred_match(self):
        """If no preferred analysts are available, return all available."""
        result = select_analysts_for_regime("high_volatility", ["warren_buffett"], min_analysts=1)
        # "technicals" not available, so min fill from all available
        assert len(result) >= 1

    def test_returns_subset_of_available(self):
        """Output is always a subset of available_analysts."""
        available = ["warren_buffett", "technicals", "fundamentals"]
        result = select_analysts_for_regime("high_volatility", available)
        assert all(a in available for a in result)

    def test_empty_available_returns_empty(self):
        result = select_analysts_for_regime("momentum", [])
        assert result == []

    def test_preferred_analysts_included(self):
        """Preferred analysts for a regime are present when available."""
        available = ["warren_buffett", "technicals", "sentiment", "fundamentals"]
        result = select_analysts_for_regime("high_volatility", available)
        # technicals and sentiment are preferred for high_volatility
        preferred_in_available = {"technicals", "sentiment"}
        assert preferred_in_available.issubset(set(result))

    def test_unknown_regime_string_defaults_to_all(self):
        """An unmapped regime string falls back to all analysts."""
        result = select_analysts_for_regime("some_future_regime", _ALL_ANALYSTS)
        assert set(result) == set(_ALL_ANALYSTS)
