"""Tests for src/risk/drawdown_guardrail.py — RISK-02."""

import pytest

from src.risk.drawdown_guardrail import compute_cppi_floor, compute_cppi_multiplier


class TestComputeCppiFloor:
    def test_floor_calculation(self):
        assert compute_cppi_floor(100_000.0, 0.20) == pytest.approx(80_000.0)

    def test_default_limit(self):
        assert compute_cppi_floor(100_000.0) == pytest.approx(80_000.0)


class TestComputeCppiMultiplier:
    def test_full_cushion_returns_one(self):
        assert compute_cppi_multiplier(100_000.0, 100_000.0, 0.20) == pytest.approx(1.0)

    def test_at_floor_returns_zero(self):
        assert compute_cppi_multiplier(80_000.0, 100_000.0, 0.20) == pytest.approx(0.0)

    def test_half_cushion(self):
        assert compute_cppi_multiplier(90_000.0, 100_000.0, 0.20) == pytest.approx(0.5)

    def test_below_floor_returns_zero(self):
        assert compute_cppi_multiplier(79_000.0, 100_000.0, 0.20) == pytest.approx(0.0)

    def test_above_peak_capped_at_one(self):
        assert compute_cppi_multiplier(110_000.0, 100_000.0, 0.20) == pytest.approx(1.0)

    def test_zero_peak_returns_neutral(self):
        assert compute_cppi_multiplier(0.0, 0.0, 0.20) == pytest.approx(1.0)

    def test_default_limit(self):
        assert compute_cppi_multiplier(100_000.0, 100_000.0) == pytest.approx(1.0)

    @pytest.mark.parametrize(
        "portfolio,peak",
        [(100_000.0, 100_000.0), (90_000.0, 100_000.0), (80_000.0, 100_000.0), (50_000.0, 100_000.0)],
    )
    def test_result_in_range(self, portfolio, peak):
        result = compute_cppi_multiplier(portfolio, peak, 0.20)
        assert 0.0 <= result <= 1.0
