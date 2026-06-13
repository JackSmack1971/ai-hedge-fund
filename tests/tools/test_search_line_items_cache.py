"""Regression tests for #161 — search_line_items caching."""

from unittest.mock import Mock, patch


class TestSearchLineItemsCache:
    @patch("src.tools.api._cache")
    @patch("src.tools.api.requests.post")
    def test_cache_hit_skips_api_call(self, mock_post, mock_cache):
        """If cache has data, no POST request should be made."""
        from src.tools.api import search_line_items

        cached_items = [{"ticker": "AAPL", "report_period": "2024-12-31", "period": "annual", "currency": "USD"}]
        mock_cache.get_line_items.return_value = cached_items

        result = search_line_items("AAPL", ["revenue", "gross_profit"], "2024-12-31")

        mock_post.assert_not_called()
        assert len(result) == 1
        assert result[0].ticker == "AAPL"

    @patch("src.tools.api._cache")
    @patch("src.tools.api.requests.post")
    def test_cache_miss_calls_api_and_stores(self, mock_post, mock_cache):
        """On cache miss, API is called and results stored."""
        from src.tools.api import search_line_items

        mock_cache.get_line_items.return_value = None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "search_results": [
                {
                    "ticker": "AAPL",
                    "report_period": "2024-12-31",
                    "period": "annual",
                    "currency": "USD",
                    "revenue": 394_328_000_000,
                }
            ]
        }
        mock_post.return_value = mock_response

        result = search_line_items("AAPL", ["revenue"], "2024-12-31")

        assert mock_post.call_count == 1
        assert len(result) == 1
        mock_cache.set_line_items.assert_called_once()

    @patch("src.tools.api._cache")
    @patch("src.tools.api.requests.post")
    def test_cache_key_sorts_line_items(self, mock_post, mock_cache):
        """Cache key sorts line_items so order doesn't create duplicate entries."""
        from src.tools.api import search_line_items

        mock_cache.get_line_items.return_value = None
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"search_results": []}
        mock_post.return_value = mock_response

        search_line_items("AAPL", ["revenue", "gross_profit"], "2024-12-31")
        first_key = mock_cache.get_line_items.call_args[0][0]

        mock_cache.reset_mock()
        mock_cache.get_line_items.return_value = None
        mock_post.return_value = mock_response

        search_line_items("AAPL", ["gross_profit", "revenue"], "2024-12-31")
        second_key = mock_cache.get_line_items.call_args[0][0]

        assert first_key == second_key

    @patch("src.tools.api._cache")
    @patch("src.tools.api.requests.post")
    def test_different_line_items_different_key(self, mock_post, mock_cache):
        """Different line_items produce different cache keys."""
        from src.tools.api import search_line_items

        mock_cache.get_line_items.return_value = None
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"search_results": []}
        mock_post.return_value = mock_response

        search_line_items("AAPL", ["revenue"], "2024-12-31")
        key_a = mock_cache.get_line_items.call_args[0][0]

        mock_cache.reset_mock()
        mock_cache.get_line_items.return_value = None

        search_line_items("AAPL", ["gross_profit"], "2024-12-31")
        key_b = mock_cache.get_line_items.call_args[0][0]

        assert key_a != key_b

    @patch("src.tools.api._cache")
    @patch("src.tools.api.requests.post")
    def test_api_error_returns_empty_list(self, mock_post, mock_cache):
        """Non-200 response returns empty list without caching."""
        from src.tools.api import search_line_items

        mock_cache.get_line_items.return_value = None
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = search_line_items("AAPL", ["revenue"], "2024-12-31")

        assert result == []
        mock_cache.set_line_items.assert_not_called()

    @patch("src.tools.api._cache")
    @patch("src.tools.api.requests.post")
    def test_limit_applied_to_cached_results(self, mock_post, mock_cache):
        """Cache results are truncated to requested limit."""
        from src.tools.api import search_line_items

        cached_items = [
            {"ticker": "AAPL", "report_period": f"2024-{i:02d}-31", "period": "annual", "currency": "USD"}
            for i in range(1, 6)
        ]
        mock_cache.get_line_items.return_value = cached_items

        result = search_line_items("AAPL", ["revenue"], "2024-12-31", limit=3)

        mock_post.assert_not_called()
        assert len(result) == 3

    @patch("src.tools.api._cache")
    @patch("src.tools.api.requests.post")
    def test_same_limit_and_items_share_cache_key(self, mock_post, mock_cache):
        """Same ticker/items/limit regardless of item order should use the same cache key."""
        from src.tools.api import search_line_items

        mock_cache.get_line_items.return_value = None
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"search_results": []}
        mock_post.return_value = mock_response

        search_line_items("AAPL", ["revenue", "gross_profit"], "2024-12-31", limit=5)
        first_key = mock_cache.get_line_items.call_args[0][0]

        mock_cache.reset_mock()
        mock_cache.get_line_items.return_value = None
        mock_post.return_value = mock_response

        search_line_items("AAPL", ["gross_profit", "revenue"], "2024-12-31", limit=5)
        second_key = mock_cache.get_line_items.call_args[0][0]

        assert first_key == second_key

    @patch("src.tools.api._cache")
    @patch("src.tools.api.requests.post")
    def test_different_limits_use_different_cache_keys(self, mock_post, mock_cache):
        """Different limits should use separate cache keys."""
        from src.tools.api import search_line_items

        mock_cache.get_line_items.return_value = None
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"search_results": []}
        mock_post.return_value = mock_response

        search_line_items("AAPL", ["revenue"], "2024-12-31", limit=5)
        first_key = mock_cache.get_line_items.call_args[0][0]

        mock_cache.reset_mock()
        mock_cache.get_line_items.return_value = None

        search_line_items("AAPL", ["revenue"], "2024-12-31", limit=8)
        second_key = mock_cache.get_line_items.call_args[0][0]

        assert first_key != second_key
