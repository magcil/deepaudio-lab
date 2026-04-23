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
    """Database model for a single loss value recorded during training or validation.

    One row per ``(run, epoch, split)`` combination — for example, a
    typical training run with 10 epochs and both train and validation
    splits produces 20 ``Loss`` rows. The uniqueness constraint on
    ``(run_id, epoch, split_type)`` enforces this at the database
    level, preventing accidental duplicates if a loss is logged twice.

    Linked many-to-one to a parent `Run`. Deleting the run
    cascades to delete all of its loss rows, both via the ORM
    relationship cascade on ``Run.losses`` and via ``ON DELETE CASCADE``
    on the foreign key.

    Attributes:
        id (int): Primary key, autoincremented.
        run_id (int): Foreign key to ``run.id``. Indexed, since loss
            rows are almost always queried by run (e.g. to plot a
            training curve). Deleting the referenced run deletes this
            row.
        loss (float): The scalar loss value at this epoch and split.
        epoch (int): The epoch number this loss corresponds to.
        split_type (SplitType): Which dataset split the loss was
            computed on (train or validation). Stored as a ``VARCHAR``
            with a ``CHECK`` constraint rather than a native database
            enum, for easier migration if new split types are added.
        run (Run): The parent run this loss belongs to. Back-populated
            from ``Run.losses``.
    """

    __tablename__ = "loss"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("run.id", ondelete="CASCADE"), nullable=False, index=True)
    loss = Column(Float, nullable=False)
    epoch = Column(Integer, nullable=False)
    split_type = Column(Enum(SplitType, native_enum=False), nullable=False)

    # Define relationships
    run = relationship("Run", back_populates="losses", foreign_keys=[run_id])

    # Apply uniqueness constraint
    __table_args__ = (UniqueConstraint("run_id", "epoch", "split_type", name="uq_loss_run_epoch_split"),)
