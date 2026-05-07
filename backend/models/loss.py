import enum

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from db.session import Base


class SplitType(str, enum.Enum):
    """Dataset split a loss value was computed on.

    Inherits from both `str` and `enum.StrEnum` so that
    members behave as plain strings, while still providing
    the type safety and validation of a Python enum.

    Attributes:
        train: Loss computed on the training split.
        validation: Loss computed on the validation split.
    """

    train = "train"
    validation = "validation"


class Loss(Base):
    """Represents a single loss value recorded during training or validation.

    Each record corresponds to a specific (run, epoch, split) combination,
    allowing reconstruction of training and validation loss curves over time.

    A uniqueness constraint ensures that only one loss value exists per
    (run_id, epoch, split_type).

    Attributes:
        id (int): Primary key of the loss record.
        run_id (int): Foreign key referencing the associated Run.
        loss (float): Scalar loss value for the given epoch and split.
        epoch (int): Training epoch number.
        split_type (SplitType): Dataset split (train or validation).
        run (Run): ORM relationship to the parent Run.
    """

    __tablename__ = "loss"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("run.id", ondelete="CASCADE"), nullable=False, index=True)
    loss = Column(Float, nullable=False)
    epoch = Column(Integer, nullable=False)
    split_type = Column(Enum(SplitType, native_enum=False), nullable=False)

    # Define relationships
    run = relationship("Run", back_populates="losses", foreign_keys=[run_id], passive_deletes=True)

    # Apply uniqueness constraint
    __table_args__ = (UniqueConstraint("run_id", "epoch", "split_type", name="uq_loss_run_epoch_split"),)
