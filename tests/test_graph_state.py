"""Tests for src/graph/state.py utility functions."""

import json
from unittest.mock import patch

import pytest

from src.graph.state import merge_dicts, show_agent_reasoning


class TestMergeDicts:
    def test_merges_two_dicts(self):
        result = merge_dicts({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_second_dict_wins_on_conflict(self):
        result = merge_dicts({"k": "old"}, {"k": "new"})
        assert result["k"] == "new"

    def test_empty_dicts(self):
        assert merge_dicts({}, {}) == {}

    def test_nested_dicts_merge_recursively(self):
        result = merge_dicts(
            {"analyst_signals": {"agent_a": {"AAPL": {"signal": "bullish"}}}, "count": 1},
            {"analyst_signals": {"agent_b": {"MSFT": {"signal": "bearish"}}}, "count": 2},
        )

        assert result["count"] == 2
        assert result["analyst_signals"]["agent_a"]["AAPL"]["signal"] == "bullish"
        assert result["analyst_signals"]["agent_b"]["MSFT"]["signal"] == "bearish"


class TestShowAgentReasoning:
    def test_dict_output(self, capsys):
        show_agent_reasoning({"signal": "bullish", "score": 8}, "TestAgent")
        captured = capsys.readouterr()
        assert "TestAgent" in captured.out
        assert "bullish" in captured.out

    def test_list_output(self, capsys):
        show_agent_reasoning([{"a": 1}], "ListAgent")
        captured = capsys.readouterr()
        assert "ListAgent" in captured.out

    def test_valid_json_string_output(self, capsys):
        show_agent_reasoning('{"signal": "bearish"}', "JsonAgent")
        captured = capsys.readouterr()
        assert "JsonAgent" in captured.out
        assert "bearish" in captured.out

    def test_invalid_json_string_falls_back(self, capsys):
        show_agent_reasoning("not valid json {{ ]}", "FallbackAgent")
        captured = capsys.readouterr()
        assert "FallbackAgent" in captured.out
        assert "not valid json" in captured.out
