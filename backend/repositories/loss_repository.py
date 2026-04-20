
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, ReferencedEntityNotFoundError, RepositoryError
from models.loss import Loss


def create(db: Session, loss: Loss) -> Loss:
    try:
        db.add(loss)
        db.commit()
        db.refresh(loss)
        return loss
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "foreign key" in msg:
            raise ReferencedEntityNotFoundError("Run", loss.run_id) from e
        if "unique" in msg:
            raise DuplicateEntityError(
                "Loss",
                f"run_id={loss.run_id}, epoch={loss.epoch}, split={loss.split_type}",
            ) from e
        raise RepositoryError("Failed to create loss") from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create loss") from e
    
def create_many(db: Session, losses: list[Loss]) -> list[Loss]:
    try:
        db.add_all(losses)
        db.commit()
        for loss in losses:
            db.refresh(loss)
        return losses
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        ref = losses[0]
        if "foreign key" in msg:
            raise ReferencedEntityNotFoundError("Run", ref.run_id) from e
        if "unique" in msg:
            raise DuplicateEntityError(
                "Loss",
                f"run_id={ref.run_id}, epoch={ref.epoch}",
            ) from e
        raise RepositoryError("Failed to create losses") from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create losses") from e
