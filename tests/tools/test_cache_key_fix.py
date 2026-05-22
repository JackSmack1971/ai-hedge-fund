"""Regression tests for cache key mismatch — fixes #158 (100% cache miss rate)."""

from unittest.mock import patch, MagicMock
from src.data.cache import Cache
from src.tools.api import get_prices


def _make_price_dict(date_str: str) -> dict:
    return {"open": 100.0, "high": 105.0, "low": 95.0, "close": 102.0, "volume": 1000, "time": f"{date_str}T00:00:00"}


class TestCacheKeyFix:
    def test_narrow_range_hits_wide_range_cache(self):
        """After prefetch stores a wide range, a narrow query must hit the cache."""
        cache = Cache()
        wide_data = [_make_price_dict(f"2024-0{m}-15") for m in range(1, 10)]
        cache.set_prices("AAPL", wide_data)

        # Narrow query within the wide range — must return from cache, not go to API
        cached = cache.get_prices("AAPL")
        assert cached is not None

        filtered = [p for p in cached if "2024-03-01" <= p["time"][:10] <= "2024-04-30"]
        assert len(filtered) >= 1

    def test_get_prices_reuses_cache_without_api_call(self):
        """get_prices() must not call the API when data is already cached for the ticker."""
        with patch("src.tools.api._cache") as mock_cache:
            narrow_day = [_make_price_dict("2024-06-15")]
            mock_cache.get_prices.return_value = narrow_day  # cache has data for ticker

            with patch("src.tools.api._make_api_request") as mock_api:
                result = get_prices("AAPL", "2024-06-15", "2024-06-15")
                mock_api.assert_not_called()

            assert len(result) == 1
            assert result[0].close == 102.0

    def test_get_prices_calls_api_on_cache_miss(self):
        """get_prices() must call the API when cache returns no data for the ticker."""
        with patch("src.tools.api._cache") as mock_cache:
            mock_cache.get_prices.return_value = None  # cache miss

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "ticker": "AAPL",
                "prices": [_make_price_dict("2024-06-15")],
            }

            with patch("src.tools.api._make_api_request", return_value=mock_resp):
                result = get_prices("AAPL", "2024-06-15", "2024-06-15")

            assert len(result) == 1
            mock_cache.set_prices.assert_called_once()
            # Must store under ticker key, not compound key
            call_args = mock_cache.set_prices.call_args[0]
            assert call_args[0] == "AAPL", f"Expected ticker key 'AAPL', got '{call_args[0]}'"

    def test_cache_stores_under_ticker_key_not_compound_key(self):
        """set_prices must be called with bare ticker, not 'AAPL_start_end'."""
        with patch("src.tools.api._cache") as mock_cache:
            mock_cache.get_prices.return_value = None

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "ticker": "TSLA",
                "prices": [_make_price_dict("2024-01-15")],
            }

            with patch("src.tools.api._make_api_request", return_value=mock_resp):
                get_prices("TSLA", "2024-01-01", "2024-12-31")

            key_used = mock_cache.set_prices.call_args[0][0]
            assert key_used == "TSLA", f"Compound key still used: {key_used!r}"
            assert "_" not in key_used, f"Compound key still used: {key_used!r}"

    def test_merge_deduplication_works_across_overlapping_prefetch(self):
        """_merge_data must deduplicate when same date is stored twice."""
        cache = Cache()
        batch1 = [_make_price_dict("2024-01-10"), _make_price_dict("2024-01-11")]
        batch2 = [_make_price_dict("2024-01-11"), _make_price_dict("2024-01-12")]
        cache.set_prices("MSFT", batch1)
        cache.set_prices("MSFT", batch2)

        result = cache.get_prices("MSFT")
        dates = [r["time"][:10] for r in result]
        assert len(dates) == len(set(dates)), "Duplicate dates found after merge"
        assert sorted(dates) == ["2024-01-10", "2024-01-11", "2024-01-12"]
