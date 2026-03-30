# services/training_service.py
import logging
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from deepaudiox import Trainer, AudioClassifier, audio_classification_dataset_from_dir
from deepaudiox.utils.training_utils import get_device
from schemas.train_params import TrainParams


class TrainingService:
    """Orchestrates the full audio classification training pipeline."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def perform_training(self, params: TrainParams, class_mapping: dict):
        """Execute the full training pipeline with a manual loop for frontend streaming."""
        
        device = get_device(device_index=params.gpu_index)

        model = AudioClassifier(
            num_classes=len(class_mapping),
            backbone=params.backbone,
            sample_rate=params.sampling_rate,
            pretrained=params.pretrained,
            freeze_backbone=params.freeze_backbone,
        )
        model.to(device)

        optimizer = Adam(params=model.parameters(), lr=params.learning_rate)
        scheduler = ReduceLROnPlateau(optimizer, "min")
        loss_function = nn.CrossEntropyLoss()

        train_dataset = audio_classification_dataset_from_dir(
            root_dir=params.training_data,
            sample_rate=params.sampling_rate,
            segment_duration=params.segment_duration,
            class_mapping=class_mapping,
        )

        validation_dataset = None
        if params.validation_data:
            validation_dataset = audio_classification_dataset_from_dir(
                root_dir=params.validation_data,
                sample_rate=params.sampling_rate,
                segment_duration=params.segment_duration,
                class_mapping=class_mapping,
            )

        trainer = Trainer(
            train_dset=train_dataset,
            validation_dset=validation_dataset,
            model=model,
            optimizer=optimizer,
            learning_rate=params.learning_rate,
            lr_scheduler=scheduler,
            loss_function=loss_function,
            epochs=params.epochs,
            patience=params.patience,
            num_workers=params.workers,
            batch_size=params.batch_size,
            path_to_checkpoint=f"{params.checkpoint}.pt",
            device_index=params.gpu_index
        )


        
        self.logger.info("Starting manual training loop...")

        # 1. Fire the "on_train_start" lifecycle hook
        for cb in trainer.callbacks:
            cb.on_train_start(trainer)

        # 2. The Manual Training Loop
        for epoch in range(1, trainer.epochs + 1):
            
            # Check for early stopping triggered in the previous epoch
            if trainer.state.early_stop:
                self.logger.info("Early stopping triggered. Halting training.")
                break
            
            # Update the trainer's internal state
            trainer.state.current_epoch = epoch
            # epoch_step() automatically fires on_epoch_start and on_epoch_end
            train_loss, val_loss = trainer.epoch_step()
            self.logger.info(f"Broadcasted Epoch {epoch} stats: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            # ---------------------------------------------------------

        # 3. Fire the "on_train_end" lifecycle hook
        for cb in trainer.callbacks:
            cb.on_train_end(trainer)

        self.logger.info("Training process complete.")

if __name__ == "__main__":
    import torch
    import numpy as np
    from torch.utils.data import Dataset
    from unittest.mock import patch
    from dataclasses import dataclass

    # 1. Create a dummy params class 
    @dataclass
    class MockTrainParams:
        epochs: int = 2
        gpu_index: int = 0 if torch.cuda.is_available() else None
        backbone: str = "beats" # deepaudiox backbone
        sampling_rate: int = 16000
        pretrained: bool = False # False makes initialization instant
        freeze_backbone: bool = False
        learning_rate: float = 1e-3
        checkpoint: str = "dummy_checkpoint"
        patience: int = 3
        training_data: str = "fake_train_path" 
        validation_data: str = "fake_val_path"
        segment_duration: float = 1.0
        workers: int = 0
        batch_size: int = 2

    # 2. Build an in-memory PyTorch dataset using numpy arrays
# 2. Build an in-memory PyTorch dataset using numpy arrays
    class DummyTensorDataset(Dataset):
        def __len__(self):
            return 8  

        def __getitem__(self, idx):
            label = int(np.random.randint(0, 2))
            
            return {
                # REMOVED THE "1," HERE to make it a flat 1D array of shape (16000,)
                "feature": np.random.randn(16000).astype(np.float32), 
                "y_true": label,
                "class_name": "class_a" if label == 0 else "class_b"
            }

    # 3. Setup our inputs
    params = MockTrainParams()
    class_mapping = {"class_a": 0, "class_b": 1}
    dummy_dataset = DummyTensorDataset()

    # 4. This line changes audio_classification_dataset_from_dir function with the dummy dataset. Just for now.
    with patch('__main__.audio_classification_dataset_from_dir', return_value=dummy_dataset):
        print("Starting in-memory tensor test...")
        try:
            service = TrainingService()
            service.perform_training(params=params, class_mapping=class_mapping)
            print("\n✅ SUCCESS: The training loop ran perfectly with dummy tensors!")
        except Exception as e:
            print(f"\n❌ FAILED: An error occurred: {e}")
            raise e
        
