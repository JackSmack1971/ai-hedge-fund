"""Unit tests for the flow-run service layer and route delegation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.backend.models.schemas import FlowRunStatus
from app.backend.services.flow_run_service import FlowRunService


def _mock_request(status=None, results=None, error_message=None):
    request = MagicMock()
    request.status = status
    request.results = results
    request.error_message = error_message
    return request


def test_flow_run_routes_delegate_to_service_layer():
    """The route module should delegate flow-run orchestration to the service layer."""
    source = Path("app/backend/routes/flow_runs.py").read_text(encoding="utf-8")
    assert "FlowRunService(" in source
    assert "FlowRepository(" not in source
    assert "FlowRunRepository(" not in source


@patch("app.backend.services.flow_run_service.process_flow_run_task")
@patch("app.backend.services.flow_run_service.FlowRunRepository")
def test_create_flow_run_queues_task(mock_repo_cls, mock_task):
    """Creating a flow run should queue the task after the queued state is stored."""
    db = MagicMock()
    mock_repo = MagicMock()
    created = MagicMock(id=42)
    queued = MagicMock(id=42)
    mock_repo.create_flow_run.return_value = created
    mock_repo.update_flow_run.return_value = queued
    mock_repo_cls.return_value = mock_repo

    service = FlowRunService(db)
    result = service.create_flow_run(7, {"mode": "test"})

    assert result is queued
    mock_repo.create_flow_run.assert_called_once_with(flow_id=7, request_data={"mode": "test"})
    mock_repo.update_flow_run.assert_called_once_with(run_id=42, status=FlowRunStatus.QUEUED)
    mock_task.delay.assert_called_once_with(42)


@patch("app.backend.services.flow_run_service.FlowRunRepository")
def test_create_flow_run_missing_flow_returns_404(mock_repo_cls):
    """Missing parent flows should be surfaced as 404s without route-level checks."""
    db = MagicMock()
    db.rollback = MagicMock()
    mock_repo = MagicMock()
    mock_repo.create_flow_run.side_effect = IntegrityError("stmt", "params", Exception("fk"))
    mock_repo_cls.return_value = mock_repo

    service = FlowRunService(db)

    with pytest.raises(HTTPException) as excinfo:
        service.create_flow_run(7, {"mode": "test"})

    assert excinfo.value.status_code == 404
    assert "Flow not found" in excinfo.value.detail
    db.rollback.assert_called_once()


@patch("app.backend.services.flow_run_service.FlowRunRepository")
def test_service_uses_single_lookup_for_run_operations(mock_repo_cls):
    """Flow/run lookups should be delegated through the service with the flow_id filter applied."""
    db = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_flow_run_by_id.return_value = MagicMock(flow_id=7)
    mock_repo.update_flow_run.return_value = MagicMock(flow_id=7)
    mock_repo.get_flow_runs_by_flow_id.return_value = [MagicMock()]
    mock_repo.get_active_flow_run.return_value = MagicMock(flow_id=7)
    mock_repo.get_latest_flow_run.return_value = MagicMock(flow_id=7)
    mock_repo.get_flow_run_count.return_value = 1
    mock_repo.delete_flow_run.return_value = True
    mock_repo.delete_flow_runs_by_flow_id.return_value = 1
    mock_repo_cls.return_value = mock_repo

    service = FlowRunService(db)

    assert service.get_flow_runs(7) == [mock_repo.get_flow_runs_by_flow_id.return_value[0]]
    assert service.get_active_flow_run(7) is mock_repo.get_active_flow_run.return_value
    assert service.get_latest_flow_run(7) is mock_repo.get_latest_flow_run.return_value
    assert service.get_flow_run(7, 9) is mock_repo.get_flow_run_by_id.return_value
    assert service.update_flow_run(7, 9, _mock_request(status=FlowRunStatus.COMPLETE)) is mock_repo.update_flow_run.return_value
    assert service.delete_flow_run(7, 9) == {"message": "Flow run deleted successfully"}
    assert service.delete_all_flow_runs(7) == {"message": "Deleted 1 flow runs successfully"}
    assert service.get_flow_run_count(7) == {"flow_id": 7, "total_runs": 1}

    mock_repo.get_flow_runs_by_flow_id.assert_called_once_with(7, limit=50, offset=0)
    mock_repo.get_active_flow_run.assert_called_once_with(7)
    mock_repo.get_latest_flow_run.assert_called_once_with(7)
    mock_repo.get_flow_run_by_id.assert_called_once_with(9, flow_id=7)
    mock_repo.update_flow_run.assert_called_once_with(
        run_id=9,
        flow_id=7,
        status=FlowRunStatus.COMPLETE,
        results=None,
        error_message=None,
    )
    mock_repo.delete_flow_run.assert_called_once_with(9, flow_id=7)
    mock_repo.delete_flow_runs_by_flow_id.assert_called_once_with(7)
    mock_repo.get_flow_run_count.assert_called_once_with(7)
