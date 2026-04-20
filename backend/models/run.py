import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.session import Base


class TaskType(str, enum.StrEnum):
    """Kind of task work a run represents.

    Inherits from both `str` and `enum.StrEnum` so that
    members behave as plain strings, while still providing 
    the type safety and validation of a Python enum.

    Attributes:
        train: A training run that produces a model checkpoint.
        evaluation: An evaluation run that loads a checkpoint and
            computes metrics on a test set.
    """
    train = "train"
    evaluation = "evaluation"

class Run(Base):
    """Database model for a single training or evaluation run.

    Acts as the central record for an experiment. Both training and
    evaluation runs live in this table, distinguished by`task_type`. 
    Each run owns its own configuration (`TrainParams` or `EvaluationParams`) 
    and any artifacts produced during execution (loss history, classification report).

    Runs may be linked to one another via `parent_run_id`, which
    is a self-referential foreign key. The typical use case is an
    evaluation run pointing to the train run whose checkpoint it
    evaluates, allowing eval results to be traced back to the
    originating training experiment. The link is optional and uses
    ``ON DELETE SET NULL`` so that deleting a parent run preserves
    its children (they simply lose the back-reference).

    Cascading deletes are configured so that removing a run also
    removes its owned configuration and artifacts (train params,
    evaluation params, losses, classification report), but does **not**
    remove its child runs — those are valuable historical records that
    should outlive their parent.

    Attributes:
        id (int): Primary key, autoincremented.
        name (str): Human-readable, unique identifier for the run.
        description (str | None): Optional decription of what the run is for.
        task_type (TaskType): Whether this is a training or
            evaluation run. Stored as a ``VARCHAR`` with a ``CHECK``
            constraint rather than a native database enum, for easier
            migration if new task types are added.
        created_at (datetime): Timestamp when the row was inserted,
            set by the database via ``server_default=func.now()``.
        parent_run_id (int | None): Optional self-referential foreign
            key to another run. Used to link an evaluation run to the
            train run that produced its checkpoint. Indexed for
            efficient lookup of a run's children.
        train_params (TrainParams | None): One-to-one configuration
            for a training run. Cascades on delete.
        evaluation_params (EvaluationParams | None): One-to-one
            configuration for an evaluation run. Cascades on delete.
        losses (list[Loss]): All loss values recorded during this run,
            across epochs and splits. Cascades on delete.
        classification_report (ClassificationReport | None): One-to-one
            evaluation report produced for this run. Cascades on delete.
        parent_run (Run | None): The run this run was derived from
            (e.g. the train run a given evaluation run was built on).
            ``None`` for top-level runs.
        child_runs (list[Run]): Runs that were derived from this one
            (e.g. all evaluation runs that use this train run's
            checkpoint). Not cascaded on delete; children survive their
            parent and have their ``parent_run_id`` set to ``NULL``.
    """
    __tablename__ = "run"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    task_type = Column(Enum(TaskType, native_enum=False), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    parent_run_id = Column(
        Integer,
        ForeignKey("run.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Define relationships
    train_params = relationship(
        "TrainParams", 
        back_populates="run", 
        cascade="all, delete-orphan",
        uselist=False
    )

    evaluation_params = relationship(
        "EvaluationParams", 
        back_populates="run", 
        cascade="all, delete-orphan",
        uselist=False
    )

    losses = relationship(
        "Loss", 
        back_populates="run", 
        cascade="all, delete-orphan"
    )

    classification_report = relationship(
        "ClassificationReport", 
        back_populates="run", 
        cascade="all, delete-orphan",
        uselist=False
    )

    parent_run = relationship(
        "Run",
        remote_side="Run.id",
        back_populates="child_runs",
        foreign_keys=[parent_run_id],
    )

    child_runs = relationship(
        "Run",
        back_populates="parent_run",
        foreign_keys=[parent_run_id],
        cascade="save-update, merge"
    )