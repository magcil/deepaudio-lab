# services/training_service.py
import logging
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn
from deepaudiox import AudioClassifier, audio_classification_dataset_from_dir
from deepaudiox.callbacks.checkpointer import Checkpointer
from deepaudiox.callbacks.early_stopper import EarlyStopper
from deepaudiox.utils.training_utils import get_device, pad_collate_fn, random_split_audio_dataset
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader


@dataclass
class TrainingState:
    """Stores mutable state tracked throughout the training lifecycle.

    Attributes:
        current_epoch: The current training epoch.
        lowest_loss: The lowest validation loss observed so far.
        train_loss: Ordered list of average training losses per epoch.
        validation_loss: Ordered list of average validation losses per epoch.
        early_stop: Flag indicating whether early stopping has been triggered.
    """
    current_epoch: int = 1
    lowest_loss: float = np.inf
    train_loss: list[float] = field(default_factory=list)
    validation_loss: list[float] = field(default_factory=list)
    early_stop: bool = False


class TrainingService:
    """Orchestrates the full audio classification training pipeline."""
    def __init__(self):
        """Initialize the training service with a fresh training state and logger."""
        self.state = TrainingState()
        self.logger = logging.getLogger(__name__)
    
    def _resolve_dataloaders(
        self, 
        train_dset, 
        validation_dset, 
        batch_size, 
        num_workers
    ):
        """Build PyTorch DataLoaders for training and validation.

        If no validation dataset is provided, the training dataset is
        automatically split 80/20.

        Args:
            train_dset (AudioClassificationDataset): Training dataset.
            validation_dset (AudioClassificationDataset | None): Validation dataset,
                or None to split from training data.
            batch_size (int): Number of samples per batch.
            num_workers (int): Number of data loading workers.

        Returns:
            tuple[DataLoader, DataLoader]: Training and validation DataLoaders.
        """
        if validation_dset is None:
            train_dset, validation_dset = random_split_audio_dataset(train_dset, 0.8)

        train_dloader = DataLoader(
            train_dset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True,
            collate_fn=pad_collate_fn,
        )
        validation_dloader = DataLoader(
            validation_dset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True,
            collate_fn=pad_collate_fn,
        )
        return train_dloader, validation_dloader

    def _train_step(self, dataloader):
        """Execute one training epoch.

        Args:
            dataloader (DataLoader): Training DataLoader.

        Returns:
            float: Average training loss for the epoch.
        """
        self.model.train()
        total_loss = 0.0

        for batch in dataloader:
            self.optimizer.zero_grad()
            x = batch["feature"].to(self.device)
            y_true = batch["y_true"].to(self.device)
            y_pred = self.model(x)
            batch_loss = self.loss_function(y_pred, y_true)
            batch_loss.backward()
            self.optimizer.step()
            total_loss += batch_loss.item()

        return total_loss / max(1, len(dataloader))

    def _validation_step(self, dataloader):
        """Execute one full validation epoch.

        Args:
            dataloader (DataLoader): Validation DataLoader.

        Returns:
            float: Average validation loss for the epoch.
        """
        self.model.eval()
        total_loss = 0.0

        with torch.no_grad():
            for batch in dataloader:
                x = batch["feature"].to(self.device)
                y_true = batch["y_true"].to(self.device)
                y_pred = self.model(x)
                batch_loss = self.loss_function(y_pred, y_true)
                total_loss += batch_loss.item()

        return total_loss / max(1, len(dataloader))

    def perform_training(self, params):
        """Execute the full training pipeline.

        Args:
            params (TrainParams): Training configuration
        """
        self.epochs = params.epochs
        self.device = get_device(device_index=params.gpu_index)

        self.model = AudioClassifier(
            num_classes=len(params.class_mapping),
            backbone=params.backbone,
            sample_rate=params.sample_rate,
            pretrained=params.pretrained,
            freeze_backbone=params.freeze_backbone,
        )
        self.model.to(self.device)

        self.optimizer = Adam(params=self.model.parameters(), lr=params.learning_rate)
        self.scheduler = ReduceLROnPlateau(self.optimizer, "min")
        self.loss_function = nn.CrossEntropyLoss()

        self.callbacks = [
            Checkpointer(path_to_checkpoint=params.checkpoint, logger=self.logger),
            EarlyStopper(patience=params.patience, logger=self.logger),
        ]

        train_dataset = audio_classification_dataset_from_dir(
            root_dir=params.training_data,
            sample_rate=params.sample_rate,
            segment_duration=params.segment_duration,
            class_mapping=params.class_mapping,
        )

        validation_dataset = None
        if params.validation_data:
            validation_dataset = audio_classification_dataset_from_dir(
                root_dir=params.validation_data,
                sample_rate=params.sample_rate,
                segment_duration=params.segment_duration,
                class_mapping=params.class_mapping,
            )

        train_dloader, validation_dloader = self._resolve_dataloaders(
            train_dset=train_dataset,
            validation_dset=validation_dataset,
            batch_size=params.batch_size,
            num_workers=params.workers,
        )

        for cb in self.callbacks:
            cb.on_train_start(self)

        for epoch in range(1, self.epochs + 1):
            if self.state.early_stop:
                break

            self.state.current_epoch = epoch

            for cb in self.callbacks:
                cb.on_epoch_start(self)

            train_loss = self._train_step(train_dloader)
            val_loss = self._validation_step(validation_dloader)

            if isinstance(self.scheduler, ReduceLROnPlateau):
                self.scheduler.step(val_loss)
            else:
                self.scheduler.step()

            self.state.train_loss.append(train_loss)
            self.state.validation_loss.append(val_loss)

            for cb in self.callbacks:
                cb.on_epoch_end(self)

        for cb in self.callbacks:
            cb.on_train_end(self)