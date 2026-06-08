"""Regression tests for call_llm use_json_mode logic — fixes #155."""

from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from src.llm.models import LLMModel
from src.utils.llm import call_llm


class _Signal(BaseModel):
    signal: str = "neutral"


def _make_model_info(has_json: bool) -> LLMModel:
    info = MagicMock(spec=LLMModel)
    info.has_json_mode.return_value = has_json
    return info


def _make_llm_mock(return_value):
    llm = MagicMock()
    llm.with_structured_output.return_value = llm
    llm.invoke.return_value = return_value
    return llm


@patch("src.utils.llm.get_model")
@patch("src.utils.llm.get_model_info")
def test_known_model_with_json_mode_uses_structured_output(mock_info, mock_model):
    """Known model that has json_mode must use with_structured_output."""
    mock_info.return_value = _make_model_info(has_json=True)
    llm = _make_llm_mock(_Signal())
    mock_model.return_value = llm

    call_llm("prompt", _Signal)

    llm.with_structured_output.assert_called_once_with(_Signal, method="json_mode")


@patch("src.utils.llm.get_model")
@patch("src.utils.llm.get_model_info")
@patch("src.utils.llm.extract_json_from_response")
def test_known_model_without_json_mode_uses_manual_extraction(mock_extract, mock_info, mock_model):
    """Known model without json_mode must NOT use structured output and must call extract_json."""
    mock_info.return_value = _make_model_info(has_json=False)
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content='{"signal": "bullish"}')
    mock_model.return_value = llm
    mock_extract.return_value = {"signal": "bullish"}

    result = call_llm("prompt", _Signal)

    llm.with_structured_output.assert_not_called()
    mock_extract.assert_called_once()
    assert result.signal == "bullish"


@patch("src.utils.llm.get_model")
@patch("src.utils.llm.get_model_info")
def test_unknown_model_defaults_to_json_mode(mock_info, mock_model):
    """Unknown model (model_info is None) must fall back to with_structured_output."""
    mock_info.return_value = None
    llm = _make_llm_mock(_Signal())
    mock_model.return_value = llm

    call_llm("prompt", _Signal)

    llm.with_structured_output.assert_called_once_with(_Signal, method="json_mode")
