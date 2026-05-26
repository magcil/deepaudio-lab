# routers/run.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from exceptions.exceptions import EntityNotFoundError
from models.run import EvaluationStatus, TrainingStatus
from repositories import run_repository
from schemas.user_info import UserInfo
from services import run_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/", status_code=status.HTTP_200_OK)
def get_all_runs(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    owner_id = None if user.is_admin else user.sub
    return run_service.get_all(db, owner_id=owner_id)


@router.get("/type/train", status_code=status.HTTP_200_OK)
def get_train_runs(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    owner_id = None if user.is_admin else user.sub
    return run_service.get(
        db,
        owner_id=owner_id,
        task_type="train",
        training_status=TrainingStatus.success,
        evaluation_status=[None, EvaluationStatus.failure],
    )


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    owner_id = None if user.is_admin else user.sub
    deleted = run_repository.delete(db, run_id, owner_id=owner_id)
    if not deleted:
        raise EntityNotFoundError("Run", run_id)


@router.get("/{run_id}", status_code=status.HTTP_200_OK)
def get_run(run_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    owner_id = None if user.is_admin else user.sub
    run = run_service.get_by_id(db, run_id, owner_id=owner_id)
    if run is None:
        raise EntityNotFoundError("Run", run_id)
    return run
