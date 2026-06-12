from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.backend.database import get_db
from app.backend.models.schemas import (
    ErrorResponse,
    FlowRunCreateRequest,
    FlowRunResponse,
    FlowRunSummaryResponse,
    FlowRunUpdateRequest,
)
from app.backend.services.flow_run_service import FlowRunService
from app.backend.services.graph import sanitize_request_payload

router = APIRouter(prefix="/flows/{flow_id}/runs", tags=["flow-runs"])


@router.post(
    "/",
    response_model=FlowRunResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_flow_run(flow_id: int, request: FlowRunCreateRequest, db: Session = Depends(get_db)):
    """Create a new flow run for the specified flow"""
    try:
        flow_run = FlowRunService(db).create_flow_run(
            flow_id=flow_id, request_data=sanitize_request_payload(request.request_data)
        )
        return FlowRunResponse.model_validate(flow_run)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create flow run: {str(e)}")


@router.get(
    "/",
    response_model=List[FlowRunSummaryResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flow_runs(
    flow_id: int,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip"),
    db: Session = Depends(get_db),
):
    """Get all runs for the specified flow"""
    try:
        flow_runs = FlowRunService(db).get_flow_runs(flow_id=flow_id, limit=limit, offset=offset)
        return [FlowRunSummaryResponse.model_validate(run) for run in flow_runs]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve flow runs: {str(e)}")


@router.get(
    "/active",
    response_model=Optional[FlowRunResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_active_flow_run(flow_id: int, db: Session = Depends(get_db)):
    """Get the current active (IN_PROGRESS) run for the specified flow"""
    try:
        active_run = FlowRunService(db).get_active_flow_run(flow_id=flow_id)
        return FlowRunResponse.model_validate(active_run)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active flow run: {str(e)}")


@router.get(
    "/latest",
    response_model=Optional[FlowRunResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_latest_flow_run(flow_id: int, db: Session = Depends(get_db)):
    """Get the most recent run for the specified flow"""
    try:
        latest_run = FlowRunService(db).get_latest_flow_run(flow_id=flow_id)
        return FlowRunResponse.model_validate(latest_run)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve latest flow run: {str(e)}")


@router.get(
    "/{run_id}",
    response_model=FlowRunResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow or run not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flow_run(flow_id: int, run_id: int, db: Session = Depends(get_db)):
    """Get a specific flow run by ID"""
    try:
        flow_run = FlowRunService(db).get_flow_run(flow_id=flow_id, run_id=run_id)
        return FlowRunResponse.model_validate(flow_run)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve flow run: {str(e)}")


@router.put(
    "/{run_id}",
    response_model=FlowRunResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Flow or run not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_flow_run(flow_id: int, run_id: int, request: FlowRunUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing flow run"""
    try:
        flow_run = FlowRunService(db).update_flow_run(flow_id=flow_id, run_id=run_id, request=request)
        return FlowRunResponse.model_validate(flow_run)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update flow run: {str(e)}")


@router.delete(
    "/{run_id}",
    responses={
        204: {"description": "Flow run deleted successfully"},
        404: {"model": ErrorResponse, "description": "Flow or run not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_flow_run(flow_id: int, run_id: int, db: Session = Depends(get_db)):
    """Delete a flow run"""
    try:
        return FlowRunService(db).delete_flow_run(flow_id=flow_id, run_id=run_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete flow run: {str(e)}")


@router.delete(
    "/",
    responses={
        204: {"description": "All flow runs deleted successfully"},
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_all_flow_runs(flow_id: int, db: Session = Depends(get_db)):
    """Delete all runs for the specified flow"""
    try:
        return FlowRunService(db).delete_all_flow_runs(flow_id=flow_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete flow runs: {str(e)}")


@router.get(
    "/count",
    responses={
        200: {"description": "Flow run count"},
        404: {"model": ErrorResponse, "description": "Flow not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_flow_run_count(flow_id: int, db: Session = Depends(get_db)):
    """Get the total count of runs for the specified flow"""
    try:
        return FlowRunService(db).get_flow_run_count(flow_id=flow_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get flow run count: {str(e)}")
