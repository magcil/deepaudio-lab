from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db.session import Base


class EvaluationParams(Base):
    """Database model for the parameters required for evaluation.

    Attributes:
        id (int): Primary key, autoincremented.
        run_id (int): Foreign key to ``run.id``. Unique, enforcing the
            one-to-one relationship at the database level. Deleting the
            referenced run deletes this row.
        path_to_test (str): Filesystem path to the test folder used
            for evaluation.
        path_to_checkpoint (str): Filesystem path to the model
            checkpoint to load before evaluating.
        class_mapping (dict): JSON object mapping class indices to
            human-readable class names, used to interpret model predictions.
        run (Run): The parent run these parameters belong to.
    """
    __tablename__ = "evaluation_params"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("run.id", ondelete="CASCADE"), nullable=False, unique=True)
    path_to_test = Column(String, nullable=False)
    path_to_checkpoint = Column(String, nullable=False)
    class_mapping = Column(JSON, nullable=False)

    # Define relationships
    run = relationship(
        "Run", 
        back_populates="evaluation_params",
        foreign_keys=[run_id],
    )
