from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, RepositoryError
from models.evaluation_params import EvaluationParams
from models.run import Run
from models.train_params import TrainParams


def create(db: Session, run: Run) -> Run:
    """Persist a new run row.

    Args:
        db (Session): Active SQLAlchemy session.
        run (Run): Run instance to insert. ``name`` must be unique.

    Raises:
        DuplicateEntityError: A run with the same ``name`` already exists.
        RepositoryError: Any other SQLAlchemy error while inserting.

    Returns:
        Run: The persisted run, refreshed with database-generated values.
    """
    try:
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except IntegrityError as e:
        db.rollback()
        raise DuplicateEntityError("Run", run.name) from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create run") from e


def create_with_train_params(db: Session, run: Run, train_params: TrainParams) -> tuple[Run, TrainParams]:
    """Persist a run together with its training parameters atomically.

    Both rows are inserted in the same transaction so neither is left
    orphaned if the commit fails.

    Args:
        db (Session): Active SQLAlchemy session.
        run (Run): Run instance to insert. ``name`` must be unique.
        train_params (TrainParams): Training parameters associated with
            the run.

    Raises:
        DuplicateEntityError: A run with the same ``name`` already exists.
        RepositoryError: Any other SQLAlchemy error while inserting.

    Returns:
        tuple[Run, TrainParams]: The persisted run and training
        parameters, refreshed with database-generated values.
    """
    try:
        db.add(run)
        db.add(train_params)
        db.commit()
        db.refresh(run)
        db.refresh(train_params)
        return run, train_params
    except IntegrityError as e:
        db.rollback()
        raise DuplicateEntityError("Run", run.name) from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create run with train params") from e


def create_with_evaluation_params(
    db: Session, run: Run, evaluation_params: EvaluationParams
) -> tuple[Run, EvaluationParams]:
    """Persist a run together with its evaluation parameters atomically.

    Both rows are inserted in the same transaction so neither is left
    orphaned if the commit fails.

    Args:
        db (Session): Active SQLAlchemy session.
        run (Run): Run instance to insert. ``name`` must be unique.
        evaluation_params (EvaluationParams): Evaluation parameters
            associated with the run.

    Raises:
        DuplicateEntityError: A run with the same ``name`` already exists.
        RepositoryError: Any other SQLAlchemy error while inserting.

    Returns:
        tuple[Run, EvaluationParams]: The persisted run and evaluation
        parameters, refreshed with database-generated values.
    """
    try:
        db.add(run)
        db.add(evaluation_params)
        db.commit()
        db.refresh(run)
        db.refresh(evaluation_params)
        return run, evaluation_params
    except IntegrityError as e:
        db.rollback()
        raise DuplicateEntityError("Run", run.name) from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create run with train params") from e


def get_by_id(db: Session, id: int) -> Run | None:
    """Look up a run by its primary key.

    Args:
        db (Session): Active SQLAlchemy session.
        id (int): Primary key of the run.

    Raises:
        RepositoryError: SQLAlchemy error while querying.

    Returns:
        Run | None: The matching run, or ``None`` if no row matches.
    """
    try:
        return db.query(Run).filter(Run.id == id).first()
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to fetch run by ID '{id}'") from e


def get_all(db: Session) -> list[Run]:
    """Retrieve all runs.

    Args:
        db (Session): Active SQLAlchemy session.

    Raises:
        RepositoryError: SQLAlchemy error while querying.

    Returns:
        list[Run]: All persisted runs, or an empty list if none exist.
    """
    try:
        return db.query(Run).all()
    except SQLAlchemyError as e:
        raise RepositoryError("Failed to fetch all runs") from e


def delete(db: Session, id: int) -> bool:
    """Delete a run by its primary key.

    Args:
        db (Session): Active SQLAlchemy session.
        id (int): Primary key of the run to delete.

    Raises:
        RepositoryError: SQLAlchemy error while deleting.

    Returns:
        bool: ``True`` if a row was deleted, ``False`` if no run matched.
    """
    try:
        run = db.query(Run).filter(Run.id == id).first()
        if run is None:
            return False
        db.delete(run)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to delete run with ID '{id}'") from e


def get_by_name(db: Session, name: str) -> Run | None:
    """Look up a run by its unique name.

    Args:
        db (Session): Active SQLAlchemy session.
        name (str): Unique name of the run.

    Raises:
        RepositoryError: SQLAlchemy error while querying.

    Returns:
        Run | None: The matching run, or ``None`` if no row matches.
    """
    try:
        return db.query(Run).filter(Run.name == name).first()
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to fetch run by name '{name}'") from e


def update_task_id(db: Session, run_id: int, task_id: str) -> None:
    """Attach a Celery task ID to an existing run.

    Args:
        db (Session): Active SQLAlchemy session.
        run_id (int): Primary key of the run to update.
        task_id (str): Celery task UUID returned by ``delay()``.

    Raises:
        RepositoryError: SQLAlchemy error while updating.
    """
    try:
        run = db.query(Run).filter(Run.id == run_id).first()
        if run is not None:
            run.task_id = task_id
            db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to update task_id for run '{run_id}'") from e


def get_with_task_ids(db: Session, within_hours: int = 168) -> list[Run]:
    """Retrieve runs that have an associated Celery task, up to a time window.

    Args:
        db (Session): Active SQLAlchemy session.
        within_hours (int): How far back to look. Defaults to 168 (7 days).

    Raises:
        RepositoryError: SQLAlchemy error while querying.

    Returns:
        list[Run]: Matching runs ordered by most recent first.
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=within_hours)
        return (
            db.query(Run)
            .filter(Run.task_id.isnot(None), Run.created_at >= cutoff)
            .order_by(Run.created_at.desc())
            .all()
        )
    except SQLAlchemyError as e:
        raise RepositoryError("Failed to fetch runs with task IDs") from e
