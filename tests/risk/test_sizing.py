"""Tests for src/risk/sizing.py — RISK-03."""

import pytest

from src.risk.sizing import fractional_kelly


class TestFractionalKelly:
    def test_disabled_by_default(self):
        assert fractional_kelly(0.6, 2.0) == pytest.approx(1.0)

    def test_explicitly_disabled(self):
        assert fractional_kelly(0.6, 2.0, enabled=False) == pytest.approx(1.0)

    def test_quarter_kelly_enabled(self):
        # full_kelly = (0.6*2.0 - 0.4) / 2.0 = 0.4; quarter = 0.1
        assert fractional_kelly(0.6, 2.0, enabled=True) == pytest.approx(0.1)

    def test_hard_cap_at_025(self):
        # full_kelly=(0.99*100-0.01)/100=0.9899; quarter=0.247 < 0.25 cap
        result = fractional_kelly(0.99, 100.0, enabled=True)
        assert result <= 0.25
        assert result == pytest.approx(0.9899 * 0.25, rel=1e-4)

    def test_negative_kelly_floored_to_zero(self):
        # full_kelly = (0.1*0.5 - 0.9) / 0.5 = -1.7; quarter = -0.425 -> 0.0
        assert fractional_kelly(0.1, 0.5, enabled=True) == pytest.approx(0.0)

    def test_disabled_returns_one_not_zero(self):
        assert fractional_kelly(0.1, 0.5, enabled=False) == pytest.approx(1.0)

    @pytest.mark.parametrize(
        "p,b",
        [(0.5, 1.0), (0.6, 2.0), (0.7, 3.0), (0.55, 1.5)],
    )
    def test_enabled_result_in_range(self, p, b):
        result = fractional_kelly(p, b, enabled=True)
        assert 0.0 <= result <= 0.25
