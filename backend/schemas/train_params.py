# schemas/train_params.py
from deepaudiox.schemas.types import BackboneName, DeviceName, PoolingName
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

VALID_BACKBONES: frozenset[str] = frozenset(BackboneName.__args__)
VALID_POOLINGS: frozenset[str] = frozenset(PoolingName.__args__)
VALID_DEVICES: frozenset[str] = frozenset(DeviceName.__args__)


class TrainParams(BaseModel):
    """Schema for audio classification training configuration.

    Defines all parameters required to launch a training run.
    Field aliases map camelCase frontend keys to snake_case Python names.

    Attributes:
        training_data: Path to the training data directory.
        validation_data: Path to the validation data directory. If None,
            the training set is automatically split 80/20.
        sampling_rate: Audio sample rate in Hz.
        segment_duration: Duration in seconds to segment audio clips.
            If None, full audio clips are used.
        backbone: Name of the backbone model architecture.
        pretrained: Whether to load pretrained weights for the backbone.
        freeze_backbone: Whether to freeze backbone parameters during training.
        pooling: Pooling strategy applied to backbone output.
        num_classes: Number of target classes.
        checkpoint: Filename for saving the best model checkpoint.
        epochs: Maximum number of training epochs.
        patience: Number of epochs without improvement before early stopping.
        learning_rate: Learning rate for the optimizer.
        workers: Number of workers for data loading.
        batch_size: Number of samples per training batch.
        gpu_index: Index of the GPU device to use.
        device: Device type for training ('cuda' or 'cpu').
        class_mapping: String path to the JSON file with the class mapping dictionary.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        alias_generator=to_camel,
    )

    training_data: str
    validation_data: str | None = Field(default=None)
    sampling_rate: int = Field(default=16_000, gt=0)
    segment_duration: float | None = Field(default=None, gt=0)
    backbone: str
    pretrained: bool = Field(default=False)
    freeze_backbone: bool = Field(default=False)
    pooling: str = Field(default="gap")
    num_classes: int = Field(gt=0)
    checkpoint: str | None = Field(default=None)
    epochs: int = Field(default=10, gt=0)
    patience: int = Field(default=5, ge=0)
    learning_rate: float = Field(default=1e-3, gt=0)
    workers: int = Field(default=2, ge=0)
    batch_size: int = Field(default=8, gt=0)
    gpu_index: int | None = Field(default=None, ge=0)
    device: str = Field(default="cpu")
    class_mapping: str
    experiment_name: str = Field(min_length=1)
    description: str | None = Field(default=None)
    parent_run_name: str | None = Field(default=None)

    @field_validator("device", mode="before")
    @classmethod
    def normalize_device(cls, v: str) -> str:
        if v == "gpu":
            return "cuda"
        return v

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
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
        if v not in VALID_BACKBONES:
            raise ValueError(f"Invalid backbone '{v}'. Must be one of: {sorted(VALID_BACKBONES)}")
        return v

    @field_validator("pooling", mode="before")
    @classmethod
    def handle_null_pooling(cls, v) -> str:
        if v is None:
            return "gap"
        return v

    @field_validator("pooling")
    @classmethod
    def validate_pooling(cls, v: str) -> str:
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
