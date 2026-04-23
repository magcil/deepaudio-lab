# schemas/evaluation_params.py
from deepaudiox.schemas.types import DeviceName
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

VALID_DEVICES: frozenset[str] = frozenset(DeviceName.__args__)


class EvaluationParams(BaseModel):
    """Schema for audio classification evaluation configuration.

    Defines all parameters required to launch an evaluation run.
    Field aliases map camelCase frontend keys to snake_case Python names.

    Attributes:
        evaluation_data: Path to the evaluation data directory.
        sampling_rate: Audio sample rate in Hz.
        segment_duration: Duration in seconds to segment audio clips.
            If None, full audio clips are used.
        num_classes: Number of target classes.
        model_checkpoint: Path to the pretrained weights.
        workers: Number of workers for data loading.
        batch_size: Number of samples per batch.
        gpu_index: Index of the GPU device to use.
        device: Device type for evaluation ('cuda' or 'cpu').
        class_mapping: String path to the JSON file with the class mapping dictionary.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_camel)

    evaluation_data: str
    sampling_rate: int = Field(default=16_000)
    segment_duration: float | None = Field(default=None)
    device: str = Field(default="cpu")
    gpu_index: int | None = Field(default=0)
    workers: int = Field(default=2)
    model_checkpoint: str
    num_classes: int
    batch_size: int = Field(default=8)
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

    @field_validator("gpu_index", mode="before")
    @classmethod
    def handle_null_gpu_index(cls, v) -> int:
        if v is None:
            return 0
        return v
