# routers/run.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from exceptions.exceptions import EntityNotFoundError
from services import run_service

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/", status_code=status.HTTP_200_OK)
def get_all_runs(db: Session = Depends(get_db)):
    """Retrieve all runs.

    Args:
        db (Session, optional): SQLAlchemy session injected by FastAPI
            via the ``get_db`` dependency.

    Returns:
        list[dict]: All persisted runs as a list of serialized run objects.
    """
    return run_service.get_all(db)


@router.get("/type/train", status_code=status.HTTP_200_OK)
def get_train_runs(db: Session = Depends(get_db)):
    """Retrieve all train runs.

    Args:
        db (Session, optional): SQLAlchemy session injected by FastAPI
            via the ``get_db`` dependency.

    Returns:
        list[dict]: All runs with task_type 'train'.
    """
    return run_service.get_all(db, task_type="train")


@router.get("/{run_id}", status_code=status.HTTP_200_OK)
def get_run(run_id: int, db: Session = Depends(get_db)):
    """Retrieve all information about a single run.

    Args:
        run_id (int): Primary key of the run to retrieve.
        db (Session, optional): SQLAlchemy session injected by FastAPI
            via the ``get_db`` dependency.

    Raises:
        EntityNotFoundError: No run with the given ``run_id`` exists.

    Returns:
        dict: The run's fields plus train params, loss history,
        and classification report.
    """
    run = run_service.get_by_id(db, run_id)
    if run is None:
        raise EntityNotFoundError("Run", run_id)
    return run