"""Tests for request-scoped LLM API keys."""

from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from src.utils.llm import call_llm, reset_request_api_keys, set_request_api_keys


class _Signal(BaseModel):
    signal: str = "neutral"


@patch("src.utils.llm.get_model")
@patch("src.utils.llm.get_model_info", return_value=None)
def test_call_llm_uses_request_context_api_keys(mock_info, mock_get_model):
    llm = MagicMock()
    llm.with_structured_output.return_value = llm
    llm.invoke.return_value = _Signal()
    mock_get_model.return_value = llm

    token = set_request_api_keys({"OPENAI_API_KEY": "context-key"})
    try:
        result = call_llm("prompt", _Signal)
    finally:
        reset_request_api_keys(token)

    assert result.signal == "neutral"
    assert mock_get_model.call_args.args[2] == {"OPENAI_API_KEY": "context-key"}
