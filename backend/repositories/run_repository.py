from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, RepositoryError
from models.experiment_params import ExperimentParams
from models.run import Run, TrainingStatus, EvaluationStatus


def create_run_with_params(db: Session, run: Run, exp_params: ExperimentParams) -> Run:
    """Create a Run together with its associated ExperimentParams in one transaction.

    Establishes a one-to-one relationship between Run and ExperimentParams and
    persists both entities atomically.

    Args:
        db (Session): Active SQLAlchemy session.
        run (Run): Run instance to persist.
        exp_params (ExperimentParams): Experiment parameters linked to the run.

    Raises:
        DuplicateEntityError: If a run with the same name already exists.
        RepositoryError: If any database error occurs during transaction.

    Returns:
        Run: The persisted Run instance with its related ExperimentParams loaded.
    """
    try:
        run.experiment_params = exp_params

        db.add(run)
        db.commit()

        db.refresh(run)
        db.refresh(exp_params)

        return run

    except IntegrityError as e:
        db.rollback()
        raise DuplicateEntityError("Run", run.name) from e

    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create run with params") from e


def get_by_id(db: Session, id: int) -> Run | None:
    """Retrieve a Run by its primary key.

    Args:
        db (Session): Active SQLAlchemy session.
        id (int): Primary key of the Run.

    Raises:
        RepositoryError: If a database query error occurs.

    Returns:
        Run | None: Matching Run instance or None if not found.
    """
    try:
        return db.query(Run).filter(Run.id == id).first()
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to fetch run by ID '{id}'") from e


def get_all(db: Session) -> list[Run]:
    """Retrieve all Run records from the database.

    Args:
        db (Session): Active SQLAlchemy session.

    Raises:
        RepositoryError: If a database query error occurs.

    Returns:
        list[Run]: List of all stored Run instances.
    """
    try:
        return db.query(Run).all()
    except SQLAlchemyError as e:
        raise RepositoryError("Failed to fetch all runs") from e


def get_query(db: Session, **filters) -> list[Run]:
    """Retrieve runs filtered by dynamic Run fields.

    Args:
        db (Session): Active SQLAlchemy session.
        **filters: Dynamic Run field/value filters. ``None`` values are ignored.

    Raises:
        RepositoryError: If a filter field is invalid or the query fails.

    Returns:
        list[Run]: List of matching Run instances.
    """
    try:
        query_filters = {}

        for field, value in filters.items():
            if value is None:
                continue

            column = Run.__mapper__.columns.get(field)
            if column is None:
                raise RepositoryError(f"Invalid query field '{field}' for Run")

            enum_class = getattr(column.type, "enum_class", None)
            if enum_class is not None and isinstance(value, str):
                matched_value = next(
                    (member for member in enum_class if value in {member.name, member.value}),
                    None,
                )
                if matched_value is None:
                    raise RepositoryError(f"Invalid value '{value}' for Run field '{field}'")
                value = matched_value

            query_filters[field] = value

        return db.query(Run).filter_by(**query_filters).all()
    except SQLAlchemyError as e:
        raise RepositoryError("Failed to fetch runs with dynamic filters") from e


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
    """Retrieve a Run by its unique name.

    Args:
        db (Session): Active SQLAlchemy session.
        name (str): Unique name of the run.

    Raises:
        RepositoryError: If a database query error occurs.

    Returns:
        Run | None: Matching Run instance or None if not found.
    """
    try:
        return db.query(Run).filter(Run.name == name).first()
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to fetch run by name '{name}'") from e


def get_by_type(db: Session, type: str) -> list[Run]:
    """Fetch all runs matching the given task type.

    Args:
        db (Session): SQLAlchemy database session.
        type (str): Task type to filter by.

    Raises:
        SQLAlchemyError: If the database query fails.

    Returns:
        list[Run]: List of Run objects matching the given type.
    """
    try:
        hasEvaluation = type == "evaluation"
        return db.query(Run).filter(Run.has_evaluation == hasEvaluation).all()
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to fetch runs with task type '{type}'") from e


def update_run(db: Session, run: Run) -> Run:
    """Commits any pending changes to the given Run instance and returns the refreshed object.

    Args:
        db (Session): The SQLAlchemy database session.
        run (Run): The Run instance with pending changes to be committed.

    Raises:
        RepositoryError: If the commit or refresh operation fails due to a database error.

    Returns:
        Run: The updated and refreshed Run instance.
    """
    try:
        db.commit()
        db.refresh(run)
        return run

    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to update run") from e


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


def update_training_status(db: Session, run_id: int, training_status: str) -> None:
    """Update the training_status to an existing run.

    Args:
        db (Session): Active SQLAlchemy session.
        run_id (int): Primary key of the run to update.
        training_status (str): db trainining status.

    Raises:
        RepositoryError: SQLAlchemy error while updating.
    """
    try:
        run = db.query(Run).filter(Run.id == run_id).first()
        if run is not None:
            run.training_status = training_status
            db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to update training_status for run '{run_id}'") from e
    
def update_evaluation_status(db: Session, run_id: int, evaluation_status: str) -> None:
    """Update the training_status to an existing run.

    Args:
        db (Session): Active SQLAlchemy session.
        run_id (int): Primary key of the run to update.
        evaluation_status (str): db evaluation status.

    Raises:
        RepositoryError: SQLAlchemy error while updating.
    """
    try:
        run = db.query(Run).filter(Run.id == run_id).first()
        if run is not None:
            run.evaluation_status = evaluation_status
            db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to update evaluation_status for run '{run_id}'") from e

def get_with_task_ids(db: Session, within_hours: int = 24) -> list[Run]:
    """Retrieve runs that have an associated Celery task, up to a time window.

    Args:
        db (Session): Active SQLAlchemy session.
        within_hours (int): How far back to look. Defaults to 24 hours, matching
            Celery's default result_expires so Redis entries are guaranteed present.

    Raises:
        RepositoryError: SQLAlchemy error while querying.

    Returns:
        list[Run]: Matching runs ordered by most recent first.
    """
    try:
        cutoff = datetime.now(UTC) - timedelta(hours=within_hours)
        return (
            db.query(Run)
            .filter(Run.task_id.isnot(None), Run.created_at >= cutoff)
            .order_by(Run.created_at.desc())
            .all()
        )
    except SQLAlchemyError as e:
        raise RepositoryError("Failed to fetch runs with task IDs") from e
