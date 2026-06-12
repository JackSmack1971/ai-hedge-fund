"""Business logic for flow run endpoints."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.backend.models.schemas import FlowRunStatus
from app.backend.repositories.flow_run_repository import FlowRunRepository
from app.backend.tasks.flow_run_tasks import process_flow_run_task


class FlowRunService:
    """Encapsulate flow-run orchestration away from the FastAPI routes."""

    def __init__(self, db: Session):
        self.db = db
        self.run_repo = FlowRunRepository(db)

    def create_flow_run(self, flow_id: int, request_data):
        """Create a queued flow run or return 404 if the parent flow is missing."""
        try:
            flow_run = self.run_repo.create_flow_run(flow_id=flow_id, request_data=request_data)
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(status_code=404, detail="Flow not found") from exc

        flow_run = self.run_repo.update_flow_run(run_id=flow_run.id, status=FlowRunStatus.QUEUED) or flow_run
        process_flow_run_task.delay(flow_run.id)
        return flow_run

    def get_flow_runs(self, flow_id: int, limit: int = 50, offset: int = 0):
        """Return flow runs or raise 404 when none exist."""
        flow_runs = self.run_repo.get_flow_runs_by_flow_id(flow_id, limit=limit, offset=offset)
        if not flow_runs:
            raise HTTPException(status_code=404, detail="Flow not found")
        return flow_runs

    def get_active_flow_run(self, flow_id: int):
        """Return the active flow run or raise 404 when none exist."""
        active_run = self.run_repo.get_active_flow_run(flow_id)
        if not active_run:
            raise HTTPException(status_code=404, detail="Flow not found")
        return active_run

    def get_latest_flow_run(self, flow_id: int):
        """Return the latest flow run or raise 404 when none exist."""
        latest_run = self.run_repo.get_latest_flow_run(flow_id)
        if not latest_run:
            raise HTTPException(status_code=404, detail="Flow not found")
        return latest_run

    def get_flow_run(self, flow_id: int, run_id: int):
        """Return a specific run or raise 404 when it does not match the flow."""
        flow_run = self.run_repo.get_flow_run_by_id(run_id, flow_id=flow_id)
        if not flow_run:
            raise HTTPException(status_code=404, detail="Flow run not found")
        return flow_run

    def update_flow_run(self, flow_id: int, run_id: int, request):
        """Update a run in a single lookup."""
        flow_run = self.run_repo.update_flow_run(
            run_id=run_id,
            flow_id=flow_id,
            status=request.status,
            results=request.results,
            error_message=request.error_message,
        )
        if not flow_run:
            raise HTTPException(status_code=404, detail="Flow run not found")
        return flow_run

    def delete_flow_run(self, flow_id: int, run_id: int):
        """Delete a run in a single lookup."""
        success = self.run_repo.delete_flow_run(run_id, flow_id=flow_id)
        if not success:
            raise HTTPException(status_code=404, detail="Flow run not found")
        return {"message": "Flow run deleted successfully"}

    def delete_all_flow_runs(self, flow_id: int):
        """Delete all runs for a flow."""
        deleted_count = self.run_repo.delete_flow_runs_by_flow_id(flow_id)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Flow not found")
        return {"message": f"Deleted {deleted_count} flow runs successfully"}

    def get_flow_run_count(self, flow_id: int):
        """Return the flow-run count or 404 when no runs exist."""
        count = self.run_repo.get_flow_run_count(flow_id)
        if count == 0:
            raise HTTPException(status_code=404, detail="Flow not found")
        return {"flow_id": flow_id, "total_runs": count}
