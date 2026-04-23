from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, RepositoryError
from models.train_params import TrainParams


def create(db: Session, train_params: TrainParams) -> TrainParams:
    """Persist a training-parameters row for an existing run.

    Args:
        db (Session): Active SQLAlchemy session.
        train_params (TrainParams): Training parameters to insert.
            ``run_id`` must reference an existing run and at most one
            ``TrainParams`` row may exist per run.

    Raises:
        DuplicateEntityError: Training parameters already exist for the
            given ``run_id``.
        RepositoryError: Any other SQLAlchemy error while inserting.

    Returns:
        TrainParams: The persisted row, refreshed with database-generated
        values.
    """
    try:
        db.add(train_params)
        db.commit()
        db.refresh(train_params)
        return train_params
    except IntegrityError as e:
        db.rollback()
        raise DuplicateEntityError("TrainParams", f"run_id={train_params.run_id}") from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create train params") from e
