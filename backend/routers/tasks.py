from datetime import datetime

from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.service import get_current_user
from db.session import get_db
from repositories import run_repository
from schemas.user_info import UserInfo
from worker.app import celery_app

router = APIRouter(prefix="/tasks", tags=["Tasks"])

ACTIVE_STATES = {"PENDING", "STARTED", "PROGRESS"}
DISPLAY_STATES = ACTIVE_STATES | {"FAILURE"}


class ActiveTask(BaseModel):
    task_id: str
    run_id: int
    experiment_name: str
    task_type: str
    created_at: datetime
    state: str
    info: dict | None = None


@router.get("/", response_model=list[ActiveTask])
def get_active_tasks(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Return active and recently failed tasks visible to the authenticated user.

    Queries two sets of runs:
    - Training/evaluation runs created within the last 24 hours.
    - Any run with an active deployment task (no time window).

    Args:
        db (Session): SQLAlchemy database session.
        user (UserInfo): The authenticated user resolved by `get_current_user`.

    Returns:
        list[ActiveTask]: Active or failed tasks with state and progress metadata.
    """
    owner_id = None if user.is_admin else user.sub
    result = []

    # Training / evaluation tasks — 24 h window is sufficient since these are
    # always created and run in the same session.
    for run in run_repository.get_with_task_ids(db, owner_id=owner_id):
        entry = _make_task_entry(run.task_id, run, run.task_type.value)
        if entry:
            result.append(entry)

    # Deployment tasks — no time window; deployments can be triggered on runs
    # created days or weeks ago.
    seen_run_ids = {e.run_id for e in result}
    for run in run_repository.get_with_deploy_task_ids(db, owner_id=owner_id):
        entry = _make_task_entry(run.deploy_task_id, run, "deployment")
        if entry and run.id not in seen_run_ids:
            result.append(entry)

    return result


def _make_task_entry(task_id: str | None, run, task_type: str) -> ActiveTask | None:
    if not task_id:
        return None
    ar = AsyncResult(task_id, app=celery_app)
    if ar.state not in DISPLAY_STATES:
        return None
    if isinstance(ar.info, Exception):
        info = {"error": str(ar.info)}
    elif isinstance(ar.info, dict):
        info = ar.info
    else:
        info = None
    return ActiveTask(
        task_id=task_id,
        run_id=run.id,
        experiment_name=run.name,
        task_type=task_type,
        created_at=run.created_at,
        state=ar.state,
        info=info,
    )
