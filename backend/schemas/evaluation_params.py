# schemas/evaluation_params.py
from deepaudiox.schemas.types import DeviceName
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
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

    train_run_id: int
    test_set: str
    device: str = Field(default="cpu")
    gpu_index: int | None = Field(default=None)
    workers: int = Field(default=2)
    batch_size: int = Field(default=8)

    @field_validator("device", mode="before")
    @classmethod
    def normalize_device(cls, v: str) -> str:
        """Normalize device aliases before validation.

        Converts user-friendly or frontend-provided device names into
        canonical values expected by the backend. Currently maps
        ``"gpu"`` to ``"cuda"`` while leaving other values unchanged.

        Args:
            v (str): Raw device value provided in the request payload.

        Returns:
            str: Normalized device string to be validated in the next step.
        """
        if v == "gpu":
            return "cuda"
        return v

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate that the device is supported.

        Ensures the provided device matches one of the allowed values
        defined in :data:`VALID_DEVICES`.

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
    def clear_gpu_index_for_non_cuda(self) -> "EvaluationParams":
        if self.device != "cuda":
            self.gpu_index = None
        return self


class EvaluationOptionsResponse(BaseModel):
    """Schema for the available evaluation device options."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    gpu_indexes: list[int]
    cuda_available: bool
    mps_available: bool
