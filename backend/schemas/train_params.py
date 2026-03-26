# schemas/train_params.py
from pydantic import BaseModel


class TrainParams(BaseModel):
    """Schema for audio classification training configuration.

    Defines all parameters required to launch a training run.

    Attributes:
        training_data: Path to the training data directory.
        validation_data: Path to the validation data directory. If None,
            the training set is automatically split 80/20.
        sample_rate: Audio sample rate in Hz.
        segment_duration: Duration in seconds to segment audio clips.
            If None, full audio clips are used.
        backbone: Name of the backbone model architecture.
        pretrained_backbone: Whether to load pretrained weights for the backbone.
        freeze_backbone: Whether to freeze backbone parameters during training.
        pooling: Pooling strategy applied to backbone output.
        num_classes: Number of target classes.
        checkpoint_name: Filename for saving the best model checkpoint.
        epochs: Maximum number of training epochs.
        patience: Number of epochs without improvement before early stopping.
        lr: Learning rate for the optimizer.
        num_workers: Number of workers for data loading.
        batch_size: Number of samples per training batch.
        device_index: Index of the GPU device to use.
        device: Device type for training (e.g. 'cuda', 'cpu').
        class_mapping: Dictionary mapping class names to integer labels.
    """
    training_data: str
    validation_data: str | None = None
    sample_rate: int = 16_000
    segment_duration: float | None = None
    backbone: str
    pretrained_backbone: bool = False
    freeze_backbone: bool = False
    pooling: str = "gap"
    num_classes: int
    checkpoint_name: str
    epochs: int = 10
    patience: int = 5
    lr: float = 1e-3
    num_workers: int = 2
    batch_size: int = 8
    device_index: int = 0
    device: str
    class_mapping: dict