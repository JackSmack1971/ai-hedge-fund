"""Regression tests for shared parsing helpers."""

from pathlib import Path

from src.utils.parsing import parse_hedge_fund_response


def test_parse_hedge_fund_response_logs_json_errors(caplog):
    """Invalid JSON should return None and log an error."""
    with caplog.at_level("ERROR"):
        result = parse_hedge_fund_response("not-json")

    assert result is None
    assert "JSON decoding error" in caplog.text


def test_shared_parser_imports_are_deduplicated():
    """Main and backend graph modules should import the shared parser helper."""
    main_source = Path("src/main.py").read_text(encoding="utf-8")
    graph_source = Path("app/backend/services/graph.py").read_text(encoding="utf-8")

    assert "from src.utils.parsing import parse_hedge_fund_response" in main_source
    assert "from src.utils.parsing import parse_hedge_fund_response" in graph_source
    assert "def parse_hedge_fund_response" not in main_source
    assert "def parse_hedge_fund_response" not in graph_source
