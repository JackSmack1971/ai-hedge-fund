"""Regression tests for warren_buffett.py fixes — #134 (pricing power) and #135 (max_score)."""

from unittest.mock import MagicMock
from src.agents.warren_buffett import (
    analyze_pricing_power,
    analyze_fundamentals,
    analyze_consistency,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _line_item(gross_profit=None, revenue=None, net_income=None, gross_margin=None):
    m = MagicMock()
    m.gross_profit = gross_profit
    m.revenue = revenue
    m.net_income = net_income
    m.gross_margin = gross_margin
    return m


def _metric(**kwargs):
    m = MagicMock()
    for k, v in kwargs.items():
        setattr(m, k, v)
    m.model_dump.return_value = {}
    return m


# ── Issue #134 — pricing power always zero ───────────────────────────────────

class TestAnalyzePricingPower:
    def test_high_gross_margin_scores_nonzero(self):
        """Company with gross_profit/revenue > 50% must get a nonzero score."""
        items = [_line_item(gross_profit=600, revenue=1000) for _ in range(5)]
        metrics = [_metric()]
        result = analyze_pricing_power(items, metrics)
        assert result["score"] > 0, "Expected non-zero score for 60% gross margin"

    def test_gross_margin_computed_from_gross_profit_and_revenue(self):
        """gross_margin = gross_profit / revenue, NOT item.gross_margin attribute."""
        items = [_line_item(gross_profit=700, revenue=1000, gross_margin=None) for _ in range(5)]
        metrics = [_metric()]
        result = analyze_pricing_power(items, metrics)
        assert result["score"] > 0, "Must compute margin from gross_profit/revenue even when gross_margin is None"

    def test_zero_revenue_is_skipped(self):
        """Items with revenue=0 must not cause ZeroDivisionError."""
        items = [_line_item(gross_profit=100, revenue=0)]
        metrics = [_metric()]
        result = analyze_pricing_power(items, metrics)
        assert isinstance(result, dict)

    def test_missing_gross_profit_is_skipped(self):
        items = [_line_item(gross_profit=None, revenue=1000)]
        metrics = [_metric()]
        result = analyze_pricing_power(items, metrics)
        assert result["score"] == 0

    def test_declining_margins_penalized(self):
        """Declining gross margin trend (recent < older) should score <= stable high margins."""
        # item[0] = most recent; gross_profit rising from old to new = DECLINING in func's view
        # (func reads recent_avg = gross_margins[:2] vs older_avg = gross_margins[-2:])
        # Declining: item[0] lowest, item[4] highest → recent < older
        declining = [_line_item(gross_profit=700 + i * 50, revenue=1000) for i in range(5)]
        declining_result = analyze_pricing_power(declining, [_metric()])
        stable = [_line_item(gross_profit=800, revenue=1000) for _ in range(5)]
        stable_result = analyze_pricing_power(stable, [_metric()])
        assert declining_result["score"] <= stable_result["score"]


# ── Issue #135 — max_possible_score components ────────────────────────────────

class TestMaxScoreKeys:
    def test_analyze_fundamentals_returns_max_score_7(self):
        metrics = [_metric(
            return_on_equity=0.20,
            debt_to_equity=0.3,
            operating_margin=0.20,
            current_ratio=2.0,
        )]
        result = analyze_fundamentals(metrics)
        assert result.get("max_score") == 7

    def test_analyze_fundamentals_empty_returns_max_score_7(self):
        result = analyze_fundamentals([])
        assert result.get("max_score") == 7

    def test_analyze_consistency_returns_max_score_3(self):
        items = [_line_item(net_income=100 + i * 10) for i in range(5)]
        result = analyze_consistency(items)
        assert result.get("max_score") == 3

    def test_analyze_consistency_insufficient_data_returns_max_score_3(self):
        result = analyze_consistency([_line_item(net_income=100)])
        assert result.get("max_score") == 3

    def test_fundamentals_perfect_score_is_7(self):
        """Maximum achievable score from analyze_fundamentals is 7."""
        metrics = [_metric(
            return_on_equity=0.25,
            debt_to_equity=0.2,
            operating_margin=0.25,
            current_ratio=2.5,
        )]
        result = analyze_fundamentals(metrics)
        assert result["score"] == 7

    def test_consistency_perfect_score_is_3(self):
        """Maximum achievable score from analyze_consistency is 3."""
        # Net income strictly increasing: [10, 20, 30, 40, 50] — reversed so item[0] is newest
        items = [_line_item(net_income=50 - i * 10) for i in range(5)]
        result = analyze_consistency(items)
        assert result["score"] == 3
