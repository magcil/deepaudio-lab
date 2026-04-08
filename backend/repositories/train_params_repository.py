from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, RepositoryError
from models.train_params import TrainParams


def create(db: Session, train_params: TrainParams) -> TrainParams:
    try:
        db.add(train_params)
        db.commit()
        db.refresh(train_params)
        return train_params
    except IntegrityError as e:
        db.rollback()
        raise DuplicateEntityError(
            "TrainParams", f"run_id={train_params.run_id}"
        ) from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create train params") from e
