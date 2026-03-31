# schemas/train_params.py
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


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

    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_camel)

    training_data: str
    validation_data: str | None = Field(default=None)
    sampling_rate: int = Field(default=16_000)
    segment_duration: float | None = Field(default=None)
    backbone: str
    pretrained: bool = Field(default=False)
    freeze_backbone: bool = Field(default=False)
    pooling: str = Field(default="gap")
    num_classes: int
    checkpoint: str | None = Field(default=None)
    epochs: int = Field(default=10)
    patience: int = Field(default=5)
    learning_rate: float = Field(default=1e-3)
    workers: int = Field(default=2)
    batch_size: int = Field(default=8)
    gpu_index: int | None = Field(default=0)
    device: str = Field(default="cpu")
    class_mapping: str

    @field_validator("device", mode="before")
    @classmethod
    def normalize_device(cls, v: str) -> str:
        if v == "gpu":
            return "cuda"
        return v

    @field_validator("gpu_index", mode="before")
    @classmethod
    def handle_null_gpu_index(cls, v) -> int:
        if v is None:
            return 0
        return v

class TrainingOptionsResponse(BaseModel):
    """Schema for the available training options.
    
    Returns lists of available backbones, pooling methods, and GPU indexes.
    Field aliases map camelCase frontend keys to snake_case Python names.
    """
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    backbones: list[str]
    pooling_methods: list[str]
    gpu_indexes: list[int]