
from deepaudiox.modules.pooling import POOLING
from deepaudiox.schemas.types import BackboneName
from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, validates

from db.session import Base

# Dynamically built enum of supported by backbone and pooling names, sourced from DeepAudioX
VALID_BACKBONES: frozenset[str] = frozenset(BackboneName.__args__)
VALID_POOLINGS: frozenset[str] = frozenset(POOLING.keys())

class TrainParams(Base):
    """Database model for the parameters required for training.

    Captures every hyperparameter and path needed to reproduce a
    training job: data loading settings, optimization hyperparameters,
    audio preprocessing parameters, model architecture choices, and
    filesystem locations for inputs and outputs. Linked one-to-one to
    a parent :class:`Run` — each training run has exactly one set of
    train params, and deleting the run cascades to delete its params
    both at the ORM level and at the database level..

    Attributes:
        id (int): Primary key, autoincremented.
        run_id (int): Foreign key to ``run.id``. Unique, enforcing the
            one-to-one relationship at the database level. Deleting the
            referenced run deletes this row.
        class_mapping (dict): JSON object mapping class indices to
            human-readable class names (or vice versa), used to
            interpret model outputs and label the training data.
        batch_size (int): Number of samples per training batch.
            Defaults to 8.
        num_workers (int): Number of subprocesses used by the data
            loader. Defaults to 2.
        epochs (int): Maximum number of epochs to train for.
            Defaults to 10.
        patience (int): Number of epochs with no improvement on the
            validation metric before early stopping triggers.
            Defaults to 5.
        lr (float): Initial learning rate for the optimizer.
            Defaults to 1e-3.
        sample_rate (int): Audio sample rate in Hz that inputs are
            resampled to before training. Defaults to 16,000.
        segment_duration (float | None): Length in seconds of audio
            segments fed to the model. ``None`` means use full-length clips.
        n_classes (int): Number of output classes. Should be consistent
            with ``class_mapping``.
        backbone (BACKBONES_ENUM): Name of the backbone architecture to
            use, validated against the dynamically built enum of
            supported backbones.
        pretrained_backbone (bool): Whether to initialize the backbone
            from pretrained weights.
        pooling (POOLINGS_ENUM): Name of the pooling strategy applied
            on top of the backbone, validated against the dynamically
            built enum of supported pooling layers. Defaults to
            ``"gap"`` (global average pooling).
        freeze_backbone (bool): If ``True``, the backbone's weights are
            frozen and only the head is trained.
        path_to_checkpoint (str): Filesystem path where the trained
            model checkpoint will be saved.
        path_to_train (str): Filesystem path to the training dataset folder.
        path_to_validation (str | None): Optional filesystem path to a
            validation dataset folder. ``None`` extracts a validation split from train.
        device (str): Compute device to train on. Defaults to "cpu".
        gpu_index (int): Index of the GPU to use when ``device`` is a
            CUDA device. Defaults to 0.
        run (Run): The parent run these parameters belong to.
            Back-populated from ``Run.train_params``.
    """
    __tablename__ = "train_params"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(
        Integer,
        ForeignKey("run.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    class_mapping = Column(JSON, nullable=False)
    batch_size = Column(Integer, nullable=False, default=8)
    num_workers = Column(Integer, nullable=False, default=2)
    epochs = Column(Integer, nullable=False, default=10)
    patience = Column(Integer, nullable=False, default=5)
    lr = Column(Float, nullable=False, default=1e-3)
    sample_rate = Column(Integer, nullable=False, default=16_000)
    segment_duration = Column(Float)
    n_classes = Column(Integer, nullable=False)
    backbone = Column(String, nullable=False)
    pretrained_backbone = Column(Boolean, nullable=False)
    pooling = Column(String, nullable=False, default="gap")
    freeze_backbone = Column(Boolean, nullable=False)
    path_to_checkpoint = Column(String, nullable=False)
    path_to_train = Column(String, nullable=False)
    path_to_validation = Column(String)
    device = Column(String, default="cpu")
    gpu_index = Column(Integer, default=0)

    run = relationship(
        "Run",
        back_populates="train_params",
        foreign_keys=[run_id],
    )

    @validates("backbone")
    def _validate_backbone(self, key: str, value: str) -> str:
        if value not in VALID_BACKBONES:
            raise ValueError(
                f"Invalid backbone '{value}'. "
                f"Must be one of: {sorted(VALID_BACKBONES)}"
            )
        return value

    @validates("pooling")
    def _validate_pooling(self, key: str, value: str) -> str:
        if value not in VALID_POOLINGS:
            raise ValueError(
                f"Invalid pooling '{value}'. "
                f"Must be one of: {sorted(VALID_POOLINGS)}"
            )
        return value