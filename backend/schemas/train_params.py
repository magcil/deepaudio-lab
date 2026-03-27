# schemas/train_params.py
import json

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
        sample_rate: Audio sample rate in Hz.
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
        device: Device type for training ('cuda' or 'cpu'). Frontend may send 'gpu'.
        class_mapping: Dictionary mapping class names to integer labels.
            Frontend may send this as a JSON-encoded string.
    """
    model_config = ConfigDict(extra='ignore', populate_by_name=True, alias_generator=to_camel)

    training_data: str = Field(alias='trainingData')
    validation_data: str | None = Field(default=None, alias='validationData')
    sample_rate: int = Field(default=16_000, alias='samplingRate')
    segment_duration: float | None = Field(default=None, alias='segmentDuration')
    backbone: str
    pretrained: bool = Field(default=False, alias='pretrained')
    freeze_backbone: bool = Field(default=False, alias='freezeBackbone')
    pooling: str = 'gap'
    num_classes: int = Field(alias='numClasses')
    checkpoint: str | None = Field(default=None, alias='checkpoint')
    epochs: int = 10
    patience: int = 5
    learning_rate: float = Field(default=1e-3, alias='learningRate')
    workers: int = Field(default=2, alias='workers')
    batch_size: int = Field(default=8, alias='batchSize')
    gpu_index: int | None = Field(default=0, alias='gpuIndex')
    device: str
    # class_mapping: dict | None = Field(default=None, alias='classMapping')
    class_mapping: str

    # @field_validator('device', mode='before')
    # @classmethod
    # def normalize_device(cls, v: str) -> str:
    #     if v == 'gpu':
    #         return 'cuda'
    #     return v

    # @field_validator('gpu_index', mode='before')
    # @classmethod
    # def handle_null_gpu_index(cls, v) -> int:
    #     if v is None:
    #         return 0
    #     return v

    # @field_validator('class_mapping', mode='before')
    # @classmethod
    # def parse_class_mapping(cls, v):
    #     if isinstance(v, str):
    #         return json.loads(v)
    #     return v
