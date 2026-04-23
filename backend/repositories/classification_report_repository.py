from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import ReferencedEntityNotFoundError, RepositoryError
from models.classification_report import ClassificationReport


def create(db: Session, report: ClassificationReport) -> ClassificationReport:
    """Persist a classification report row for a run.

    Commits the report, rolling back on failure and translating SQLAlchemy
    errors into the application's domain exceptions.

    Args:
        db (Session): Active SQLAlchemy session.
        report (ClassificationReport): Report to insert. ``run_id`` must
            reference an existing ``Run``.

    Raises:
        ReferencedEntityNotFoundError: The ``run_id`` does not reference an
            existing run (foreign-key violation).
        RepositoryError: Any other integrity or SQLAlchemy error while
            inserting the report.

    Returns:
        ClassificationReport: The persisted report, refreshed with
        database-generated values.
    """
    try:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig).lower()
        if "foreign key" in msg:
            raise ReferencedEntityNotFoundError("Run", report.run_id) from e
        raise RepositoryError("Failed to create classification report") from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create classification report") from e
