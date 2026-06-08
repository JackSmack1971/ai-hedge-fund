import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.backend.database import get_db
from app.backend.models.schemas import FlowRunStatus
from app.backend.repositories.flow_repository import FlowRepository
from app.backend.repositories.flow_run_repository import FlowRunRepository

router = APIRouter(prefix="/flows/{flow_id}/runs", tags=["flow-run-events"])


@router.get("/{run_id}/events")
async def stream_flow_run_events(flow_id: int, run_id: int, db: Session = Depends(get_db)):
    """Stream flow-run status changes as Server-Sent Events."""
    flow_repo = FlowRepository(db)
    if not flow_repo.get_flow_by_id(flow_id):
        raise HTTPException(status_code=404, detail="Flow not found")

    run_repo = FlowRunRepository(db)
    flow_run = run_repo.get_flow_run_by_id(run_id)
    if not flow_run or flow_run.flow_id != flow_id:
        raise HTTPException(status_code=404, detail="Flow run not found")

    async def event_generator():
        last_status = None
        while True:
            current = run_repo.get_flow_run_by_id(run_id)
            if not current:
                yield "event: error\ndata: " + json.dumps({"message": "Flow run not found"}) + "\n\n"
                return

            if current.status != last_status:
                payload = {
                    "run_id": current.id,
                    "flow_id": current.flow_id,
                    "status": current.status,
                    "error_message": current.error_message,
                }
                yield "event: status\ndata: " + json.dumps(payload) + "\n\n"
                last_status = current.status

            if current.status in {FlowRunStatus.COMPLETE.value, FlowRunStatus.ERROR.value}:
                return

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
