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

def create_with_train_params(
    db: Session, run: Run, train_params: TrainParams
) -> tuple[Run, TrainParams]:
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
    db: Session,
    run: Run,
    evaluation_params: EvaluationParams
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