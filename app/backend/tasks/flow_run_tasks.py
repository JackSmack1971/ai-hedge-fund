from app.backend.database.connection import SessionLocal
from app.backend.models.schemas import FlowRunStatus
from app.backend.repositories.flow_run_repository import FlowRunRepository
from app.backend.tasks.celery_app import celery_app


@celery_app.task(name="app.backend.tasks.process_flow_run_task")
def process_flow_run_task(run_id: int) -> dict:
    """
    Background worker entrypoint for flow-run execution.

    This task currently updates run lifecycle status and stores a minimal result.
    """
    db = SessionLocal()
    try:
        repo = FlowRunRepository(db)
        flow_run = repo.get_flow_run_by_id(run_id)
        if not flow_run:
            return {"run_id": run_id, "status": "missing"}

        repo.update_flow_run(run_id, status=FlowRunStatus.IN_PROGRESS)
        repo.update_flow_run(
            run_id,
            status=FlowRunStatus.COMPLETE,
            results={"run_id": run_id, "message": "Flow run processed asynchronously."},
        )
        return {"run_id": run_id, "status": FlowRunStatus.COMPLETE.value}
    except Exception as exc:
        FlowRunRepository(db).update_flow_run(run_id, status=FlowRunStatus.ERROR, error_message=str(exc))
        raise
    finally:
        db.close()

