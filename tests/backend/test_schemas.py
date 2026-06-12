"""Tests for app/backend/models/schemas.py — Pydantic schema validation."""

import math

import pytest
from pydantic import ValidationError

from app.backend.models.schemas import (
    AgentModelConfig,
    BacktestRequest,
    ErrorResponse,
    FlowCreateRequest,
    FlowRunStatus,
    GraphEdge,
    GraphNode,
    HedgeFundRequest,
    PortfolioPosition,
)
from src.llm.models import ModelProvider


class TestPortfolioPosition:
    def test_valid_position(self):
        p = PortfolioPosition(ticker="AAPL", quantity=100.0, trade_price=150.0)
        assert p.ticker == "AAPL"
        assert p.quantity == 100.0

    def test_zero_price_raises(self):
        with pytest.raises(ValidationError):
            PortfolioPosition(ticker="AAPL", quantity=100.0, trade_price=0.0)

    def test_negative_price_raises(self):
        with pytest.raises(ValidationError):
            PortfolioPosition(ticker="AAPL", quantity=100.0, trade_price=-10.0)

    def test_missing_ticker_raises(self):
        with pytest.raises(ValidationError):
            PortfolioPosition(quantity=100.0, trade_price=150.0)


class TestGraphNode:
    def test_minimal_node(self):
        node = GraphNode(id="node-1")
        assert node.id == "node-1"
        assert node.type is None
        assert node.data is None

    def test_full_node(self):
        node = GraphNode(id="node-1", type="analyst", data={"key": "value"}, position={"x": 0, "y": 0})
        assert node.type == "analyst"
        assert node.data == {"key": "value"}

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            GraphNode()


class TestGraphEdge:
    def test_valid_edge(self):
        edge = GraphEdge(id="e1", source="node-1", target="node-2")
        assert edge.source == "node-1"
        assert edge.target == "node-2"

    def test_missing_source_raises(self):
        with pytest.raises(ValidationError):
            GraphEdge(id="e1", target="node-2")


class TestErrorResponse:
    def test_minimal_error(self):
        err = ErrorResponse(message="Something went wrong")
        assert err.message == "Something went wrong"
        assert err.error is None

    def test_with_error_detail(self):
        err = ErrorResponse(message="Failed", error="NullPointerException")
        assert err.error == "NullPointerException"


class TestHedgeFundRequest:
    def _minimal_request(self):
        return {
            "tickers": ["AAPL"],
            "graph_nodes": [{"id": "n1"}],
            "graph_edges": [],
            "initial_cash": 100000.0,
        }

    def test_valid_minimal_request(self):
        req = HedgeFundRequest(**self._minimal_request())
        assert req.tickers == ["AAPL"]

    def test_default_model_is_set(self):
        req = HedgeFundRequest(**self._minimal_request())
        assert req.model_name is not None

    def test_missing_tickers_raises(self):
        data = self._minimal_request()
        del data["tickers"]
        with pytest.raises(ValidationError):
            HedgeFundRequest(**data)

    def test_negative_initial_cash_raises(self):
        data = self._minimal_request()
        data["initial_cash"] = -1
        with pytest.raises(ValidationError):
            HedgeFundRequest(**data)

    def test_oversized_ticker_list_raises(self):
        data = self._minimal_request()
        data["tickers"] = [f"T{i}" for i in range(51)]
        with pytest.raises(ValidationError):
            HedgeFundRequest(**data)


class TestFlowRunStatus:
    def test_status_values(self):
        assert FlowRunStatus.QUEUED == "QUEUED"
        assert FlowRunStatus.IDLE == "IDLE"
        assert FlowRunStatus.IN_PROGRESS == "IN_PROGRESS"
        assert FlowRunStatus.COMPLETE == "COMPLETE"
        assert FlowRunStatus.ERROR == "ERROR"


class TestFlowCreateRequest:
    def test_valid_request(self):
        req = FlowCreateRequest(
            name="My Flow",
            nodes=[{"id": "n1"}],
            edges=[],
        )
        assert req.name == "My Flow"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            FlowCreateRequest(nodes=[], edges=[])


class TestBacktestRequestDates:
    def _minimal_request(self):
        return {
            "tickers": ["AAPL"],
            "graph_nodes": [{"id": "n1"}],
            "graph_edges": [],
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "initial_capital": 100000.0,
        }

    def test_valid_date_range(self):
        req = BacktestRequest(**self._minimal_request())
        assert req.start_date == "2024-01-01"
        assert req.end_date == "2024-01-02"

    def test_invalid_date_format_raises(self):
        data = self._minimal_request()
        data["start_date"] = "2024-13-01"
        with pytest.raises(ValidationError):
            BacktestRequest(**data)

    def test_reversed_dates_raise(self):
        data = self._minimal_request()
        data["start_date"] = "2024-06-01"
        data["end_date"] = "2024-01-01"
        with pytest.raises(ValidationError):
            BacktestRequest(**data)

    def test_same_dates_raise(self):
        data = self._minimal_request()
        data["start_date"] = "2024-01-01"
        data["end_date"] = "2024-01-01"
        with pytest.raises(ValidationError):
            BacktestRequest(**data)

    def test_nan_margin_requirement_raises(self):
        data = self._minimal_request()
        data["margin_requirement"] = math.nan
        with pytest.raises(ValidationError):
            BacktestRequest(**data)

    def test_negative_initial_capital_raises(self):
        data = self._minimal_request()
        data["initial_capital"] = -1
        with pytest.raises(ValidationError):
            BacktestRequest(**data)

    def test_oversized_portfolio_positions_raise(self):
        data = self._minimal_request()
        data["portfolio_positions"] = [
            {"ticker": f"T{i}", "quantity": 1.0, "trade_price": 1.0} for i in range(51)
        ]
        with pytest.raises(ValidationError):
            BacktestRequest(**data)


class TestHedgeFundRequestDates:
    def _minimal_request(self):
        return {
            "tickers": ["AAPL"],
            "graph_nodes": [{"id": "n1"}],
            "graph_edges": [],
        }

    def test_invalid_end_date_format_raises(self):
        data = self._minimal_request()
        data["end_date"] = "yesterday"
        with pytest.raises(ValidationError):
            HedgeFundRequest(**data)

    def test_start_date_must_be_before_end_date(self):
        data = self._minimal_request()
        data["start_date"] = "2024-06-01"
        data["end_date"] = "2024-01-01"
        with pytest.raises(ValidationError):
            HedgeFundRequest(**data)
