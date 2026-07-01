# schemas/train_params.py
from deepaudiox.schemas.types import BackboneName, DeviceName, PoolingName
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

VALID_BACKBONES: frozenset[str] = frozenset(BackboneName.__args__)
VALID_POOLINGS: frozenset[str] = frozenset(PoolingName.__args__)
VALID_DEVICES: frozenset[str] = frozenset(DeviceName.__args__)


class TrainParams(BaseModel):
    """Schema for audio classification training configuration.

    Defines all parameters required to launch a training run, including
    dataset paths, model architecture, optimization hyperparameters,
    and runtime configuration. Field aliases map camelCase frontend
    keys to snake_case Python names.

    Attributes:
        training_data (str): Filesystem path to the training dataset directory.
        validation_data (str | None): Optional path to a validation dataset.
            If ``None``, a validation split may be derived from training data.
        sampling_rate (int): Audio sample rate in Hz. Must be between 1 and 44100.
        segment_duration (float | None): Duration in seconds for audio
            segmentation. If ``None``, full-length clips are used.
        backbone (str): Name of the backbone architecture to use.
            Must be one of the supported values in ``VALID_BACKBONES``.
        pretrained (bool): Whether to initialize the backbone with
            pretrained weights.
        freeze_backbone (bool): Whether to freeze backbone weights
            during training.
        pooling (str): Pooling strategy applied on top of the backbone.
            Must be one of ``VALID_POOLINGS``. Defaults to ``"gap"``.
        checkpoint (str | None): Optional path to a checkpoint to resume
            training from.
        epochs (int): Number of training epochs. Must be positive.
        patience (int): Number of epochs with no improvement before
            early stopping. Must be non-negative.
        learning_rate (float): Optimizer learning rate. Must be positive.
        workers (int): Number of worker processes for data loading.
            Must be non-negative.
        batch_size (int): Number of samples per training batch.
            Must be positive.
        gpu_index (int | None): Index of the GPU device to use.
            ``None`` defaults to 0.
        device (str): Compute device to use (e.g. ``"cpu"``, ``"cuda"``).
            Must be one of ``VALID_DEVICES``.
        class_mapping (str): Path to a JSON file defining the mapping
            between class labels and indices.
        experiment_name (str): Unique name for the training run.
        description (str | None): Optional human-readable description
            of the experiment.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        alias_generator=to_camel,
    )

    dataset_id: int
    training_set: str
    validation_set: str | None = Field(default=None)
    sampling_rate: int = Field(default=16_000, gt=0, le=44_100)
    segment_duration: float | None = Field(default=None, gt=0)
    backbone: str
    pretrained: bool = Field(default=False)
    freeze_backbone: bool = Field(default=False)
    pooling: str = Field(default="gap")
    checkpoint: str | None = Field(default=None)
    epochs: int = Field(default=10, gt=0)
    patience: int = Field(default=0, ge=0)
    learning_rate: float = Field(default=1e-3, gt=0)
    workers: int = Field(default=2, ge=0)
    batch_size: int = Field(default=8, gt=0)
    gpu_index: int | None = Field(default=None, ge=0)
    device: str = Field(default="cpu")
    experiment_name: str = Field(min_length=1)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("pooling", mode="before")
    @classmethod
    def handle_null_pooling(cls, v) -> str:
        if v is None:
            return "gap"
        return v

    @field_validator("device", mode="before")
    @classmethod
    def normalize_device(cls, v: str) -> str:
        """Normalize device aliases before validation.

        Converts user-friendly device names into canonical values expected
        by the backend. Currently maps ``"gpu"`` to ``"cuda"``.

        Args:
            v (str): Raw device value from the request payload.

        Returns:
            str: Normalized device string.
        """
        if v == "gpu":
            return "cuda"
        return v

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate that the device is supported.

        Ensures the provided device is one of the allowed values defined
        in :data:`VALID_DEVICES`.

        Args:
            v (str): Normalized device string.

        Raises:
            ValueError: If the device is not supported.

        Returns:
            str: The validated device string.
        """
        if v not in VALID_DEVICES:
            raise ValueError(f"Invalid device '{v}'. Must be one of: {sorted(VALID_DEVICES)}")
        return v

    @model_validator(mode="after")
    def clear_gpu_index_for_non_cuda(self) -> "TrainParams":
        if self.device != "cuda":
            self.gpu_index = None
        return self

    @field_validator("backbone")
    @classmethod
    def validate_backbone(cls, v: str) -> str:
        """Validate that the backbone is supported.

        Args:
            v (str): Backbone name.

        Raises:
            ValueError: If the backbone is not in ``VALID_BACKBONES``.

        Returns:
            str: The validated backbone name.
        """
        if v not in VALID_BACKBONES:
            raise ValueError(f"Invalid backbone '{v}'. Must be one of: {sorted(VALID_BACKBONES)}")
        return v

    @field_validator("pooling")
    @classmethod
    def validate_pooling(cls, v: str) -> str:
        """Validate that the pooling method is supported.

        Args:
            v (str): Pooling method name.

        Raises:
            ValueError: If the pooling method is not in ``VALID_POOLINGS``.

        Returns:
            str: The validated pooling method.
        """
        if v not in VALID_POOLINGS:
            raise ValueError(f"Invalid pooling '{v}'. Must be one of: {sorted(VALID_POOLINGS)}")
        return v


class TrainingOptionsResponse(BaseModel):
    """Schema for the available training options.

    Returns lists of available backbones, pooling methods, and GPU indexes,
    plus availability flags for CUDA and MPS devices.
    Field aliases map camelCase frontend keys to snake_case Python names.
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    backbones: list[str]
    pooling_methods: list[str]
    gpu_indexes: list[int]
    cuda_available: bool
    mps_available: bool
