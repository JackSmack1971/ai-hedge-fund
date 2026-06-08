"""Regression tests for calculate_adx DataFrame mutation — fixes #133."""

import pandas as pd
import pytest

from src.agents.technicals import calculate_adx


@pytest.fixture()
def ohlcv_df():
    return pd.DataFrame(
        {
            "open": [100.0] * 30,
            "high": [105.0, 106.0, 104.0, 107.0, 103.0] * 6,
            "low": [95.0, 94.0, 96.0, 93.0, 97.0] * 6,
            "close": [102.0, 103.0, 101.0, 104.0, 100.0] * 6,
            "volume": [1000] * 30,
        }
    )


def test_calculate_adx_does_not_mutate_input(ohlcv_df):
    """calculate_adx must not add temporary columns to the caller's DataFrame."""
    original_cols = set(ohlcv_df.columns)
    calculate_adx(ohlcv_df)
    assert (
        set(ohlcv_df.columns) == original_cols
    ), f"calculate_adx mutated input: extra cols = {set(ohlcv_df.columns) - original_cols}"


def test_calculate_adx_returns_expected_columns(ohlcv_df):
    result = calculate_adx(ohlcv_df)
    assert set(result.columns) == {"adx", "+di", "-di"}


def test_calculate_adx_original_values_unchanged(ohlcv_df):
    """Values in the original DataFrame must be identical before and after the call."""
    high_before = ohlcv_df["high"].copy()
    calculate_adx(ohlcv_df)
    pd.testing.assert_series_equal(ohlcv_df["high"], high_before)


def test_calculate_adx_result_length_matches_input(ohlcv_df):
    result = calculate_adx(ohlcv_df)
    assert len(result) == len(ohlcv_df)


def test_multiple_adx_calls_produce_same_result(ohlcv_df):
    """Calling calculate_adx twice on the same DataFrame must produce identical results."""
    result1 = calculate_adx(ohlcv_df)
    result2 = calculate_adx(ohlcv_df)
    pd.testing.assert_frame_equal(result1, result2)
