# services/training_service.py
import logging

import torch.nn as nn
from deepaudiox import AudioClassifier, Trainer, audio_classification_dataset_from_dir
from deepaudiox.utils.training_utils import get_device
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

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
            device_index=params.gpu_index,
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
            self.logger.info(f"Epoch {epoch} stats: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            # ---------------------------------------------------------

        # 3. Fire the "on_train_end" lifecycle hook
        for cb in trainer.callbacks:
            cb.on_train_end(trainer)

        self.logger.info("Training process complete.")
