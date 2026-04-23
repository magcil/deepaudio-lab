from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, ReferencedEntityNotFoundError, RepositoryError
from models.loss import Loss


def create(db: Session, loss: Loss) -> Loss:
    """Persist a single loss record.

    Args:
        db (Session): Active SQLAlchemy session.
        loss (Loss): Loss row to insert, already populated with
            ``run_id``, ``epoch``, ``split_type`` and the loss value.

    Raises:
        ReferencedEntityNotFoundError: The ``run_id`` does not reference an
            existing run.
        DuplicateEntityError: A loss for the same ``(run_id, epoch, split_type)``
            combination already exists.
        RepositoryError: Any other integrity or SQLAlchemy error while
            inserting the row.

    Returns:
        Loss: The persisted loss, refreshed with database-generated values.
    """
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
    """Persist a batch of loss records in a single transaction.

    All rows are committed together so a single integrity failure rolls
    back the whole batch.

    Args:
        db (Session): Active SQLAlchemy session.
        losses (list[Loss]): Losses to insert. Assumed to share a
            common ``run_id``; the first item is used when raising
            domain-specific errors.

    Raises:
        ReferencedEntityNotFoundError: The batch references a ``run_id``
            that does not exist.
        DuplicateEntityError: At least one row collides with an existing
            ``(run_id, epoch, split_type)`` entry.
        RepositoryError: Any other integrity or SQLAlchemy error while
            inserting the batch.

    Returns:
        list[Loss]: The persisted losses, refreshed with
        database-generated values.
    """
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
