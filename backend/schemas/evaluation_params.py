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

    train_name: str
    evaluation_data: str
    device: str = Field(default="cpu")
    gpu_index: int | None = Field(default=0)
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

    @field_validator("gpu_index", mode="before")
    @classmethod
    def handle_null_gpu_index(cls, v) -> int:
        """Ensure a valid GPU index is always set.

        Converts ``None`` values (e.g. from JSON ``null``) into the
        default GPU index ``0`` so downstream code can safely assume
        an integer is always present.

        Args:
            v: Raw GPU index value from the request payload.

        Returns:
            int: A valid GPU index, defaulting to ``0`` when input is ``None``.
        """
        if v is None:
            return 0
        return v
