from sqlalchemy import JSON, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from db.session import Base


class ClassificationReport(Base):
    """Database model for a classification report produced during evaluation.

    Attributes:
        id (int): Primary key, autoincremented.
        run_id (int): Foreign key to ``run.id``. Unique, enforcing the
            one-to-one relationship at the database level. Deleting the
            referenced run deletes this report.
        report (dict): The full classification report as a JSON object.
        run (Run): The parent run this report belongs to.
    """

    __tablename__ = "classification_report"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("run.id", ondelete="CASCADE"), nullable=False, unique=True)
    report = Column(JSON, nullable=False)

    # Define relationships
    run = relationship(
        "Run",
        back_populates="classification_report",
        foreign_keys=[run_id],
    )
