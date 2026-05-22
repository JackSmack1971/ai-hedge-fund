"""Tests for src/cli/input.py — argument parsing and validation."""
import pytest

from src.cli.input import parse_tickers, select_analysts, resolve_dates


class TestParseTickers:
    def test_valid_single_ticker(self):
        assert parse_tickers("AAPL") == ["AAPL"]

    def test_valid_multiple_tickers(self):
        result = parse_tickers("AAPL,MSFT,GOOGL")
        assert result == ["AAPL", "MSFT", "GOOGL"]

    def test_strips_whitespace(self):
        result = parse_tickers(" AAPL , MSFT ")
        assert result == ["AAPL", "MSFT"]

    def test_none_returns_empty_list(self):
        assert parse_tickers(None) == []

    def test_empty_string_returns_empty_list(self):
        assert parse_tickers("") == []

    def test_single_comma_only(self):
        result = parse_tickers(",")
        assert result == []

    def test_mixed_valid_and_empty_segments(self):
        result = parse_tickers("AAPL,,MSFT")
        assert "AAPL" in result
        assert "MSFT" in result
        assert "" not in result


class TestSelectAnalysts:
    def test_analysts_all_flag_returns_all(self):
        result = select_analysts({"analysts_all": True, "analysts": None})
        assert len(result) > 0
        assert isinstance(result, list)

    def test_analysts_flag_parsed_correctly(self):
        result = select_analysts({"analysts_all": False, "analysts": "warren_buffett,charlie_munger"})
        assert "warren_buffett" in result
        assert "charlie_munger" in result

    def test_analysts_all_overrides_analysts(self):
        all_result = select_analysts({"analysts_all": True, "analysts": None})
        subset_result = select_analysts({"analysts_all": False, "analysts": "warren_buffett"})
        assert len(all_result) > len(subset_result)

    def test_analysts_strips_whitespace(self):
        result = select_analysts({"analysts_all": False, "analysts": " warren_buffett , charlie_munger "})
        assert "warren_buffett" in result
        assert "charlie_munger" in result


class TestResolveDates:
    def test_both_dates_explicit(self):
        start, end = resolve_dates("2024-01-01", "2024-03-01")
        assert start == "2024-01-01"
        assert end == "2024-03-01"

    def test_invalid_start_date_raises(self):
        with pytest.raises(ValueError):
            resolve_dates("01/01/2024", "2024-03-01")

    def test_invalid_end_date_raises(self):
        with pytest.raises(ValueError):
            resolve_dates("2024-01-01", "not-a-date")

    def test_invalid_start_date_format_raises(self):
        with pytest.raises(ValueError):
            resolve_dates("20240101", "2024-03-01")

    def test_no_start_date_uses_default_months_back(self):
        start, end = resolve_dates(None, "2024-03-01", default_months_back=3)
        assert start == "2023-12-01"
        assert end == "2024-03-01"

    def test_no_end_date_defaults_to_today(self):
        from datetime import datetime
        fixed_now = datetime(2024, 6, 15)
        _, end = resolve_dates("2024-01-01", None, _now=fixed_now)
        assert end == "2024-06-15"

    def test_both_none_uses_defaults(self):
        from datetime import datetime
        fixed_now = datetime(2024, 6, 15)
        start, end = resolve_dates(None, None, default_months_back=1, _now=fixed_now)
        assert end == "2024-06-15"
        assert start < end

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="must be before"):
            resolve_dates("2025-01-01", "2024-01-01")

    def test_start_equal_end_raises(self):
        with pytest.raises(ValueError, match="must be before"):
            resolve_dates("2024-01-01", "2024-01-01")

    def test_january_month_boundary(self):
        from datetime import datetime
        fixed_now = datetime(2024, 1, 31)
        start, end = resolve_dates(None, "2024-01-31", default_months_back=3, _now=fixed_now)
        assert start == "2023-10-31"
