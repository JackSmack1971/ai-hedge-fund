"""Tests that financial-data API failures are observable (logged) rather than silently swallowed (#20)."""

import logging
from unittest.mock import Mock, patch

import requests

from src.tools.api import get_financial_metrics, get_market_cap, get_prices


def _response(status_code=200, json_data=None, text="", json_exc=None):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.text = text
    if json_exc is not None:
        response.json.side_effect = json_exc
    else:
        response.json.return_value = json_data
    return response


def test_get_prices_http_error_is_logged(caplog):
    response = _response(status_code=401, text='{"detail": "invalid api key"}')
    with patch("src.tools.api._make_api_request", return_value=response):
        with caplog.at_level(logging.ERROR, logger="src.tools.api"):
            result = get_prices("ERRHTTP1", "2024-01-01", "2024-01-31")

    assert result == []
    assert any("401" in record.message for record in caplog.records)
    assert any("invalid api key" in record.message for record in caplog.records)


def test_get_prices_parse_error_is_logged_with_payload_snippet(caplog):
    response = _response(status_code=200, json_data={"unexpected": "shape"}, text='{"unexpected": "shape"}')
    with patch("src.tools.api._make_api_request", return_value=response):
        with caplog.at_level(logging.ERROR, logger="src.tools.api"):
            result = get_prices("ERRPARSE1", "2024-01-01", "2024-01-31")

    assert result == []
    assert any("unexpected" in record.message for record in caplog.records)


def test_get_prices_invalid_json_is_logged(caplog):
    response = _response(
        status_code=200,
        text="<html>gateway timeout</html>",
        json_exc=requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0),
    )
    with patch("src.tools.api._make_api_request", return_value=response):
        with caplog.at_level(logging.ERROR, logger="src.tools.api"):
            result = get_prices("ERRJSON1", "2024-01-01", "2024-01-31")

    assert result == []
    assert any("gateway timeout" in record.message for record in caplog.records)


def test_get_prices_genuine_empty_result_is_not_logged_as_error(caplog):
    response = _response(status_code=200, json_data={"ticker": "EMPTY1", "prices": []})
    with patch("src.tools.api._make_api_request", return_value=response):
        with caplog.at_level(logging.ERROR, logger="src.tools.api"):
            result = get_prices("EMPTY1", "2024-01-01", "2024-01-31")

    assert result == []
    assert caplog.records == [], "a legitimately empty result must not be reported as an error"


def test_get_financial_metrics_http_error_is_logged(caplog):
    response = _response(status_code=429, text='{"detail": "rate limited"}')
    with patch("src.tools.api._make_api_request", return_value=response):
        with caplog.at_level(logging.ERROR, logger="src.tools.api"):
            result = get_financial_metrics("ERRHTTP2", "2024-01-31")

    assert result == []
    assert any("429" in record.message for record in caplog.records)


def test_get_market_cap_http_error_is_logged(caplog):
    import datetime

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    response = _response(status_code=500, text="internal error")
    with patch("src.tools.api._make_api_request", return_value=response):
        with caplog.at_level(logging.ERROR, logger="src.tools.api"):
            result = get_market_cap("ERRHTTP3", today)

    assert result is None
    assert any("500" in record.message for record in caplog.records)
