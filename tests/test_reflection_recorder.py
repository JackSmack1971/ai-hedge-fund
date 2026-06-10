"""ROUT-03 tests: reflection recorder — JSONL trace writing."""

import json
import tempfile
from pathlib import Path

import pytest

from src.reflection.recorder import ReflectionRecorder, record_trace


def _make_final_state(
    tickers=None,
    include_hybrid=True,
    include_regime=True,
):
    tickers = tickers or ["AAPL"]
    data = {
        "tickers": tickers,
        "analyst_signals": {},
    }
    if include_regime:
        data["regime_classification"] = {
            t: {
                "regime": "momentum",
                "confidence": 75,
                "reasoning": "Uptrend detected",
            }
            for t in tickers
        }
        data["regime_selection"] = {t: ["technicals", "cathie_wood"] for t in tickers}
    if include_hybrid:
        data["guardrail_outputs"] = {
            t: {
                "ticker": t,
                "raw_confidence": 70,
                "disagreement_score": 0.2,
                "subjectivity_score": 0.1,
                "herding_flag": False,
                "overconfidence_flag": False,
                "calibrated_confidence": 65,
                "confidence_multiplier": 0.85,
                "risk_flags": [],
                "reasoning": "Moderate confidence",
            }
            for t in tickers
        }
        data["meta_label_outputs"] = {
            t: {
                "ticker": t,
                "allow_trade": True,
                "size_multiplier": 0.85,
                "label": "allow",
                "reasoning": "Confidence sufficient",
            }
            for t in tickers
        }
    return {"data": data, "messages": []}


class TestRecordTrace:
    def test_writes_jsonl_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            state = _make_final_state(tickers=["AAPL"])
            record_trace(path, "2024-03-01", state)
            assert path.exists()

    def test_one_line_per_ticker(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            state = _make_final_state(tickers=["AAPL", "MSFT"])
            record_trace(path, "2024-03-01", state)
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            assert len(lines) == 2

    def test_each_line_is_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            state = _make_final_state(tickers=["AAPL", "GOOGL"])
            record_trace(path, "2024-03-01", state)
            for line in path.read_text(encoding="utf-8").strip().splitlines():
                parsed = json.loads(line)
                assert isinstance(parsed, dict)

    def test_trace_contains_ticker_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            record_trace(path, "2024-03-01", _make_final_state(tickers=["AAPL"]))
            record = json.loads(path.read_text(encoding="utf-8").strip())
            assert record["ticker"] == "AAPL"

    def test_trace_contains_regime(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            record_trace(path, "2024-03-01", _make_final_state(tickers=["AAPL"]))
            record = json.loads(path.read_text(encoding="utf-8").strip())
            assert record["regime"] is not None
            assert record["regime"]["regime"] == "momentum"

    def test_trace_contains_guardrails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            record_trace(path, "2024-03-01", _make_final_state(tickers=["AAPL"]))
            record = json.loads(path.read_text(encoding="utf-8").strip())
            assert record["guardrails"] is not None
            assert record["guardrails"]["confidence_multiplier"] == 0.85

    def test_trace_contains_meta_label(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            record_trace(path, "2024-03-01", _make_final_state(tickers=["AAPL"]))
            record = json.loads(path.read_text(encoding="utf-8").strip())
            assert record["meta_label"] is not None
            assert record["meta_label"]["label"] == "allow"

    def test_appends_across_multiple_calls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            record_trace(path, "2024-03-01", _make_final_state(tickers=["AAPL"]))
            record_trace(path, "2024-03-04", _make_final_state(tickers=["AAPL"]))
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            assert len(lines) == 2

    def test_missing_hybrid_outputs_produce_null_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            state = _make_final_state(tickers=["AAPL"], include_hybrid=False, include_regime=False)
            record_trace(path, "2024-03-01", state)
            record = json.loads(path.read_text(encoding="utf-8").strip())
            assert record["guardrails"] is None
            assert record["meta_label"] is None
            assert record["regime"] is None


class TestReflectionRecorder:
    def test_class_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "traces.jsonl"
            recorder = ReflectionRecorder(path)
            state = _make_final_state(tickers=["AAPL"])
            recorder.record("2024-03-01", state)
            assert path.exists()

    def test_total_traces_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            recorder = ReflectionRecorder(path)
            recorder.record("2024-03-01", _make_final_state(tickers=["AAPL", "MSFT"]))
            recorder.record("2024-03-04", _make_final_state(tickers=["AAPL"]))
            assert recorder.total_traces == 3

    def test_record_returns_count_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "traces.jsonl"
            recorder = ReflectionRecorder(path)
            n = recorder.record("2024-03-01", _make_final_state(tickers=["AAPL", "MSFT", "GOOGL"]))
            assert n == 3
