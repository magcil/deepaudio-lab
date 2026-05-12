import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.session import Base

class TaskType(str, enum.Enum):
    """Represents the type of execution task associated with a Run.

    Used to distinguish between training runs and evaluation runs.

    Attributes:
        train: A standard training run.
        train_evaluation: An evaluation run executed after training.
    """

    train = "train"
    train_evaluation = "evaluation"
    
class TrainingStatus(str, enum.Enum):
    """Represents the lifecycle state of a training run.

    Attributes:
        pending: Training has been created but not started yet.
        progress: Training is currently running.
        failure: Training finished with an error.
        success: Training completed successfully.
    """

    pending = 'Pending'
    progress = 'In Progress'
    failure = 'Failed'
    success = 'Successful'

class EvaluationStatus(str, enum.Enum):
    """Represents the lifecycle state of an evaluation run.

    Attributes:
        pending: Evaluation has been created but not started yet.
        progress: Evaluation is currently running.
        failure: Evaluation finished with an error.
        success: Evaluation completed successfully.
    """

    pending = 'Pending'
    progress = 'In Progress'
    failure = 'Failed'
    success = 'Successful'


class Run(Base):
    """Represents a single experiment run in the system.

    A Run is the central entity that ties together training configuration,
    training metrics, and evaluation results. It can represent either a
    training execution or a post-training evaluation.

    Attributes:
        id (int): Primary key of the run.
        name (str): Unique name identifying the run.
        description (str | None): Optional human-readable description.
        task_type (TaskType): Type of run (training or evaluation).
        task_id (str | None): Optional external task identifier for async execution.
        created_at (datetime): Timestamp when the run was created.
        training_status (TrainingStatus): Current lifecycle state of the training flow.
        evaluation_status (EvaluationStatus): Current lifecycle state of the evaluation flow.

        experiment_params (ExperimentParams): One-to-one relationship
            containing training configuration and dataset paths.
        losses (list[Loss]): Time-series training/validation loss records.
        classification_report (ClassificationReport): One-to-one evaluation
            results for the run.
        has_evaluation (bool): Whether evaluation has been executed for this run.
    """

    __tablename__ = "run"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType, native_enum=False), nullable=False)
    task_id = Column(String, nullable=True, index=True)
    has_evaluation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    training_status: Mapped[TrainingStatus] = mapped_column(Enum(TrainingStatus, native_enum=False), nullable=False)
    evaluation_status: Mapped[EvaluationStatus] = mapped_column(Enum(EvaluationStatus, native_enum=False), nullable=True)
    
    # Define relationships
    experiment_params = relationship(
        "ExperimentParams", back_populates="run", cascade="all, delete-orphan", uselist=False, passive_deletes=True
    )

    losses = relationship("Loss", back_populates="run", cascade="all, delete-orphan", passive_deletes=True)

    classification_report = relationship(
        "ClassificationReport", back_populates="run", cascade="all, delete-orphan", uselist=False, passive_deletes=True
    )
