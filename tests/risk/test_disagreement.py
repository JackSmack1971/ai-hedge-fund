"""Tests for src/risk/disagreement.py — RISK-01."""

import pytest

from src.risk.disagreement import compute_disagreement_multiplier, compute_disagreement_score


class TestComputeDisagreementScore:
    def test_unanimous_buy(self):
        assert compute_disagreement_score([1, 1, 1]) == pytest.approx(0.0)

    def test_50_50_split_max_disagreement(self):
        assert compute_disagreement_score([1, 1, -1, -1]) == pytest.approx(1.0)

    def test_unanimous_sell(self):
        assert compute_disagreement_score([-1, -1, -1]) == pytest.approx(0.0)

    def test_none_imputed_as_zero(self):
        result_none = compute_disagreement_score([1, None, -1])
        result_zero = compute_disagreement_score([1, 0, -1])
        assert result_none == pytest.approx(result_zero)

    def test_all_none_returns_zero(self):
        assert compute_disagreement_score([None, None]) == pytest.approx(0.0)

    def test_single_analyst(self):
        assert compute_disagreement_score([1]) == pytest.approx(0.0)

    def test_empty_list(self):
        assert compute_disagreement_score([]) == pytest.approx(0.0)

    @pytest.mark.parametrize(
        "stances",
        [
            [1, 1, 1],
            [-1, -1, -1],
            [1, 0, -1],
            [1, 1, -1, -1],
            [None, 1, -1],
            [0, 0, 0],
        ],
    )
    def test_result_in_range(self, stances):
        result = compute_disagreement_score(stances)
        assert 0.0 <= result <= 1.0


class TestComputeDisagreementMultiplier:
    def test_unanimous_buy_gives_full_multiplier(self):
        assert compute_disagreement_multiplier([1, 1, 1]) == pytest.approx(1.0)

    def test_50_50_split_gives_zero_multiplier(self):
        assert compute_disagreement_multiplier([1, 1, -1, -1]) == pytest.approx(0.0)

    @pytest.mark.parametrize(
        "stances",
        [
            [1, 1, 1],
            [-1, -1, -1],
            [1, 0, -1],
            [1, 1, -1, -1],
        ],
    )
    def test_result_in_range(self, stances):
        result = compute_disagreement_multiplier(stances)
        assert 0.0 <= result <= 1.0
