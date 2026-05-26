from datetime import datetime

from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from repositories import run_repository
from schemas.user_info import UserInfo
from services.auth_service import get_current_user
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
    owner_id = None if user.is_admin else user.sub
    runs = run_repository.get_with_task_ids(db, owner_id=owner_id)
    result = []
    for run in runs:
        ar = AsyncResult(run.task_id, app=celery_app)
        if ar.state not in DISPLAY_STATES:
            continue
        if isinstance(ar.info, Exception):
            info = {"error": str(ar.info)}
        elif isinstance(ar.info, dict):
            info = ar.info
        else:
            info = None
        result.append(
            ActiveTask(
                task_id=run.task_id,
                run_id=run.id,
                experiment_name=run.name,
                task_type=run.task_type.value,
                created_at=run.created_at,
                state=ar.state,
                info=info,
            )
        )
    return result
