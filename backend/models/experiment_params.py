from functools import lru_cache

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, validates

from db.session import Base


# Supported backbone/pooling names are sourced from DeepAudioX. They are imported
# LAZILY (inside these cached accessors) rather than at module load, so merely
# importing this model does not pull in deepaudiox — and therefore torch. The
# validators below only run when an attribute is assigned (in the API/training
# worker, which have deepaudiox); loading a row from the DB never triggers them,
# so the lean maintenance worker can import this model without deepaudiox.
@lru_cache(maxsize=1)
def _valid_backbones() -> frozenset[str]:
    from deepaudiox.schemas.types import BackboneName

    return frozenset(BackboneName.__args__)


@lru_cache(maxsize=1)
def _valid_poolings() -> frozenset[str]:
    from deepaudiox.modules.pooling import POOLING

    return frozenset(POOLING.keys())


class ExperimentParams(Base):
    """Stores all configuration parameters for a training experiment.

    This model is tightly coupled (one-to-one) with a Run and contains all
    hyperparameters, dataset paths, and runtime configuration required to
    reproduce or evaluate a training run.

    It also enforces validation on selected fields (e.g. backbone and pooling)
    to ensure compatibility with supported DeepAudioX configurations.

    Attributes:
        id (int): Primary key of the experiment parameters record.
        run_id (int): Foreign key to the associated Run. Unique, enforcing
            a one-to-one relationship.
        class_mapping (dict): Mapping of class labels used for training.
        batch_size (int): Training batch size.
        num_workers (int): Number of DataLoader workers.
        epochs (int): Number of training epochs.
        patience (int): Early stopping patience.
        lr (float): Learning rate.
        sample_rate (int): Audio sample rate in Hz.
        segment_duration (float | None): Duration of audio segments.
        n_classes (int): Number of output classes.
        backbone (str): Backbone architecture name.
        pretrained_backbone (bool): Whether to use pretrained weights.
        pooling (str): Pooling strategy used in the model.
        freeze_backbone (bool): Whether backbone weights are frozen.
        path_to_checkpoint (str): Path to model checkpoint.
        dataset_id (int): ID of the Dataset record used for this run.
        path_to_train (str): Path to training dataset.
        path_to_validation (str | None): Path to validation dataset.
        path_to_test (str | None): Path to test/evaluation dataset.
        device (str): Execution device (cpu/cuda).
        gpu_index (int): GPU index to use if device is cuda.
        run (Run): ORM relationship to the associated Run.

    Raises:
        ValueError: If an invalid backbone is provided.
        ValueError: If an invalid pooling method is provided.
    """

    __tablename__ = "experiment_params"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("run.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
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
    dataset_id = Column(Integer, nullable=False)
    path_to_train = Column(String, nullable=False)
    path_to_validation = Column(String)
    path_to_test = Column(String)
    device = Column(String, default="cpu")
    gpu_index = Column(Integer, default=0)

    run = relationship("Run", back_populates="experiment_params", foreign_keys=[run_id], passive_deletes=True)

    @validates("backbone")
    def _validate_backbone(self, key: str, value: str) -> str:
        """Validate that the selected backbone is supported.

        Ensures that the provided backbone name exists in the list of
        supported DeepAudioX backbones.

        Args:
            key (str): SQLAlchemy attribute name being validated ("backbone").
            value (str): Proposed backbone value.

        Raises:
            ValueError: If the backbone is not in the supported set.

        Returns:
            str: Validated backbone name.
        """
        valid = _valid_backbones()
        if value not in valid:
            raise ValueError(f"Invalid backbone '{value}'. Must be one of: {sorted(valid)}")
        return value

    @validates("pooling")
    def _validate_pooling(self, key: str, value: str) -> str:
        """Validate that the selected pooling method is supported.

        Ensures that the provided pooling strategy exists in the available
        DeepAudioX pooling implementations.

        Args:
            key (str): SQLAlchemy attribute name being validated ("pooling").
            value (str): Proposed pooling value.

        Raises:
            ValueError: If the pooling method is not supported.

        Returns:
            str: Validated pooling method.
        """
        valid = _valid_poolings()
        if value not in valid:
            raise ValueError(f"Invalid pooling '{value}'. Must be one of: {sorted(valid)}")
        return value
