from sqlalchemy import JSON, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from db.session import Base


class ClassificationReport(Base):
    """Represents the evaluation results of a single run.

    Stores the full classification report (precision, recall, f1-score, etc.)
    generated after model evaluation. This model is in a one-to-one
    relationship with a Run.

    Attributes:
        id (int): Primary key of the classification report.
        run_id (int): Foreign key referencing the associated Run. Unique,
            enforcing a one-to-one relationship.
        report (dict): JSON-serialized classification metrics produced by
            sklearn's classification_report (output_dict=True).
        run (Run): ORM relationship to the associated Run instance.
    """

    __tablename__ = "classification_report"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("run.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    report = Column(JSON, nullable=False)

    # Define relationships
    run = relationship("Run", back_populates="classification_report", foreign_keys=[run_id], passive_deletes=True)
