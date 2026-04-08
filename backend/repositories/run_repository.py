from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, RepositoryError
from models.run import Run
from models.train_params import TrainParams
from models.evaluation_params import EvaluationParams


def create(db: Session, run: Run) -> Run:
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
    
def get_by_name(db: Session, name: str) -> Run | None:
    try:
        return db.query(Run).filter(Run.name == name).first()
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to fetch run by name '{name}'") from e