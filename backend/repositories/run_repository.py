from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, RepositoryError
from models.experiment_params import ExperimentParams
from models.run import Run


def create(db: Session, run: Run) -> Run:
    """Persist a new Run record in the database.

    Args:
        db (Session): Active SQLAlchemy session.
        run (Run): Run instance to persist. Must have a unique name.

    Raises:
        DuplicateEntityError: If a run with the same name already exists.
        RepositoryError: If any database error occurs during insertion.

    Returns:
        Run: The persisted Run instance with database-generated fields populated.
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


def create_run_with_params(
    db: Session, run: Run, exp_params: ExperimentParams
) -> Run:
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
    
def update_run(
    db: Session, run: Run
) -> Run:
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