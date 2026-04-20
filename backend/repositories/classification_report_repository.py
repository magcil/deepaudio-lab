
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import ReferencedEntityNotFoundError, RepositoryError
from models.classification_report import ClassificationReport


def create(db: Session, report: ClassificationReport) -> ClassificationReport:
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