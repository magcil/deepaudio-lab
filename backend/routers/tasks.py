from datetime import datetime

from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from repositories import run_repository
from worker.app import celery_app

router = APIRouter(prefix="/tasks", tags=["Tasks"])

ACTIVE_STATES = {"PENDING", "STARTED", "PROGRESS"}


class ActiveTask(BaseModel):
    task_id: str
    run_id: int
    experiment_name: str
    task_type: str
    created_at: datetime
    state: str
    info: dict | None = None


@router.get("/", response_model=list[ActiveTask])
def get_active_tasks(db: Session = Depends(get_db)):
    """Return all runs with an associated Celery task that are still active.

    Queries runs that have a task_id, checks their current Celery state,
    and returns only those in PENDING, STARTED, or PROGRESS states.
    """
    runs = run_repository.get_with_task_ids(db)
    result = []
    for run in runs:
        ar = AsyncResult(run.task_id, app=celery_app)
        if ar.state not in ACTIVE_STATES:
            continue
        info = ar.info if isinstance(ar.info, dict) else None
        result.append(
            ActiveTask(
                task_id=run.task_id,
                run_id=run.id,
                experiment_name=run.name,
                task_type=run.task_type,
                created_at=run.created_at,
                state=ar.state,
                info=info,
            )
        )
    return result
