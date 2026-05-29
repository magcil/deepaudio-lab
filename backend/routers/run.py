# routers/run.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from exceptions.exceptions import EntityNotFoundError
from models.run import EvaluationStatus, TrainingStatus
from repositories import run_repository
from schemas.user_info import UserInfo
from services import run_service
from auth.service import get_current_user

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/", status_code=status.HTTP_200_OK)
def get_all_runs(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Return all runs visible to the authenticated user.

    Admins receive all runs in the system; regular users only receive
    runs they own.

    Args:
        db (Session): SQLAlchemy database session.
        user (UserInfo): The authenticated user resolved by `get_current_user`.

    Returns:
        list[dict]: Serialized list of runs.
    """
    owner_id = None if user.is_admin else user.sub
    return run_service.get_all(db, owner_id=owner_id)


@router.get("/type/train", status_code=status.HTTP_200_OK)
def get_train_runs(db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Return successfully completed training runs eligible for evaluation.

    Admins receive all qualifying runs; regular users only see their own.
    A run is included if its training status is successful and its
    evaluation status is either absent or previously failed.

    Args:
        db (Session): SQLAlchemy database session.
        user (UserInfo): The authenticated user resolved by `get_current_user`.

    Returns:
        list[dict]: Serialized list of qualifying training runs.
    """
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
    """Delete a run by ID.

    Admins can delete any run; regular users can only delete their own.

    Args:
        run_id (int): Primary key of the run to delete.
        db (Session): SQLAlchemy database session.
        user (UserInfo): The authenticated user resolved by `get_current_user`.

    Raises:
        EntityNotFoundError: If no run with the given ID exists, or if
            the run does not belong to the requesting user.
    """
    owner_id = None if user.is_admin else user.sub
    deleted = run_repository.delete(db, run_id, owner_id=owner_id)
    if not deleted:
        raise EntityNotFoundError("Run", run_id)


@router.get("/{run_id}", status_code=status.HTTP_200_OK)
def get_run(run_id: int, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Retrieve a single run by ID with full details.

    Admins can access any run; regular users can only access their own.

    Args:
        run_id (int): Primary key of the run to retrieve.
        db (Session): SQLAlchemy database session.
        user (UserInfo): The authenticated user resolved by `get_current_user`.

    Raises:
        EntityNotFoundError: If no run with the given ID exists, or if
            the run does not belong to the requesting user.

    Returns:
        dict: Serialized run detail including experiment parameters,
            loss history, and classification report.
    """
    owner_id = None if user.is_admin else user.sub
    run = run_service.get_by_id(db, run_id, owner_id=owner_id)
    if run is None:
        raise EntityNotFoundError("Run", run_id)
    return run
