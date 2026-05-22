"""Tests for src/utils/api_key.py."""
from src.utils.api_key import get_api_key_from_state


class TestGetApiKeyFromState:
    def test_returns_none_when_state_empty(self):
        assert get_api_key_from_state({}, "OPENAI_API_KEY") is None

    def test_returns_none_when_no_request_in_metadata(self):
        state = {"metadata": {}}
        assert get_api_key_from_state(state, "OPENAI_API_KEY") is None

    def test_returns_key_when_present(self):
        class FakeRequest:
            api_keys = {"OPENAI_API_KEY": "sk-test-123"}

        state = {"metadata": {"request": FakeRequest()}}
        result = get_api_key_from_state(state, "OPENAI_API_KEY")
        assert result == "sk-test-123"

    def test_returns_none_when_key_not_in_api_keys(self):
        class FakeRequest:
            api_keys = {"OTHER_KEY": "value"}

        state = {"metadata": {"request": FakeRequest()}}
        assert get_api_key_from_state(state, "MISSING_KEY") is None

    def test_returns_none_when_request_has_no_api_keys_attr(self):
        class FakeRequest:
            pass

        state = {"metadata": {"request": FakeRequest()}}
        assert get_api_key_from_state(state, "OPENAI_API_KEY") is None
