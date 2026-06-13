import os
from unittest.mock import call, Mock, patch

import pytest

from src.tools.api import _make_api_request, _REQUEST_TIMEOUT, get_prices


def _make_429(retry_after=None):
    """Return a mock 429 response with optional Retry-After header."""
    r = Mock()
    r.status_code = 429
    r.headers = {"Retry-After": str(retry_after)} if retry_after else {}
    return r


def _make_200():
    r = Mock()
    r.status_code = 200
    r.text = "Success"
    return r


class TestRateLimiting:
    """Test suite for API rate limiting functionality."""

    @patch("src.tools.api.time.sleep")
    @patch("src.tools.api.requests.get")
    def test_handles_single_rate_limit(self, mock_get, mock_sleep):
        """Test that API retries once after a 429 and succeeds."""
        mock_get.side_effect = [_make_429(), _make_200()]

        headers = {"X-API-KEY": "test-key"}
        url = "https://api.financialdatasets.ai/test"
        result = _make_api_request(url, headers)

        assert result.status_code == 200
        assert mock_get.call_count == 2
        mock_get.assert_has_calls(
            [
                call(url, headers=headers, params=None, timeout=_REQUEST_TIMEOUT),
                call(url, headers=headers, params=None, timeout=_REQUEST_TIMEOUT),
            ]
        )

        # Full-jitter: attempt=0 → uniform(0, min(60, 2^0)=1.0)
        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        assert 0 <= delay <= 1.0

    @patch("src.tools.api.time.sleep")
    @patch("src.tools.api.requests.get")
    def test_handles_multiple_rate_limits(self, mock_get, mock_sleep):
        """Test that API retries multiple times after 429s with exponential backoff."""
        mock_get.side_effect = [_make_429(), _make_429(), _make_429(), _make_200()]

        headers = {"X-API-KEY": "test-key"}
        url = "https://api.financialdatasets.ai/test"
        result = _make_api_request(url, headers)

        assert result.status_code == 200
        assert mock_get.call_count == 4
        assert mock_sleep.call_count == 3

        delays = [c[0][0] for c in mock_sleep.call_args_list]
        # attempt=0 → cap=1.0, attempt=1 → cap=2.0, attempt=2 → cap=4.0
        assert 0 <= delays[0] <= 1.0
        assert 0 <= delays[1] <= 2.0
        assert 0 <= delays[2] <= 4.0

    @patch("src.tools.api.time.sleep")
    @patch("src.tools.api.requests.post")
    def test_handles_post_rate_limiting(self, mock_post, mock_sleep):
        """Test that POST requests handle rate limiting."""
        mock_post.side_effect = [_make_429(), _make_200()]

        headers = {"X-API-KEY": "test-key"}
        url = "https://api.financialdatasets.ai/test"
        json_data = {"test": "data"}
        result = _make_api_request(url, headers, method="POST", json_data=json_data)

        assert result.status_code == 200
        assert mock_post.call_count == 2
        mock_post.assert_has_calls(
            [
                call(url, headers=headers, json=json_data, timeout=_REQUEST_TIMEOUT),
                call(url, headers=headers, json=json_data, timeout=_REQUEST_TIMEOUT),
            ]
        )

        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        assert 0 <= delay <= 1.0

    @patch("src.tools.api.time.sleep")
    @patch("src.tools.api.requests.get")
    def test_ignores_other_errors(self, mock_get, mock_sleep):
        """Test that non-429 errors are returned without retrying."""
        mock_500 = Mock()
        mock_500.status_code = 500
        mock_500.text = "Internal Server Error"
        mock_get.return_value = mock_500

        result = _make_api_request("https://api.financialdatasets.ai/test", {"X-API-KEY": "k"})

        assert result.status_code == 500
        assert mock_get.call_count == 1
        mock_sleep.assert_not_called()

    @patch("src.tools.api.time.sleep")
    @patch("src.tools.api.requests.get")
    def test_normal_success_requests(self, mock_get, mock_sleep):
        """Test that successful requests return immediately without retry."""
        mock_get.return_value = _make_200()

        result = _make_api_request("https://api.financialdatasets.ai/test", {})

        assert result.status_code == 200
        assert mock_get.call_count == 1
        mock_sleep.assert_not_called()

    @patch("src.tools.api.time.sleep")
    @patch("src.tools.api.requests.get")
    def test_retry_after_header_respected(self, mock_get, mock_sleep):
        """Test that Retry-After header overrides jitter calculation."""
        mock_get.side_effect = [_make_429(retry_after=5), _make_200()]

        _make_api_request("https://api.financialdatasets.ai/test", {})

        mock_sleep.assert_called_once_with(5.0)

    @patch("src.tools.api._cache")
    @patch("src.tools.api.time.sleep")
    @patch("src.tools.api.requests.get")
    def test_full_integration(self, mock_get, mock_sleep, mock_cache):
        """Test that get_prices function properly handles rate limiting."""
        mock_cache.get_prices.return_value = None

        mock_200 = Mock()
        mock_200.status_code = 200
        mock_200.json.return_value = {
            "ticker": "AAPL",
            "prices": [
                {
                    "time": "2024-01-01T00:00:00Z",
                    "open": 100.0,
                    "close": 101.0,
                    "high": 102.0,
                    "low": 99.0,
                    "volume": 1000,
                }
            ],
        }
        mock_get.side_effect = [_make_429(), mock_200]

        with patch.dict(os.environ, {"FINANCIAL_DATASETS_API_KEY": "test-key"}):
            result = get_prices("AAPL", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0].open == 100.0
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        assert 0 <= delay <= 1.0
        mock_cache.get_prices.assert_called_once()
        mock_cache.set_prices.assert_called_once()

    @patch("src.tools.api.time.sleep")
    @patch("src.tools.api.requests.get")
    def test_max_retries_exceeded(self, mock_get, mock_sleep):
        """Test that function stops retrying after max_retries and returns final 429."""
        mock_429 = _make_429()
        mock_429.text = "Too Many Requests"
        mock_get.return_value = mock_429

        result = _make_api_request("https://api.financialdatasets.ai/test", {"X-API-KEY": "k"}, max_retries=2)

        assert result.status_code == 429
        assert mock_get.call_count == 3  # 1 initial + 2 retries
        assert mock_sleep.call_count == 2

        delays = [c[0][0] for c in mock_sleep.call_args_list]
        assert 0 <= delays[0] <= 1.0  # attempt=0 → cap=1
        assert 0 <= delays[1] <= 2.0  # attempt=1 → cap=2


if __name__ == "__main__":
    pytest.main([__file__])
