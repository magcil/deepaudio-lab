# services/training_service.py
import logging
import time

import torch.nn as nn
from deepaudiox import Trainer
from deepaudiox.utils.training_utils import get_device
from sqlalchemy.orm import Session
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

from adapters.callbacks import S3Checkpointer
from adapters.classifiers import S3AudioClassifier
from adapters.dataset import S3AudioClassificationDataset
from adapters.utils import create_file_to_class_mapping_from_s3
from db.session import SessionLocal
from models.loss import Loss
from models.run import TrainingStatus
from repositories import dataset_repository, loss_repository
from repositories.run_repository import update_training_status
from schemas.train_params import TrainParams


class TrainingService:
    """Orchestrates the full audio classification training pipeline."""

    def __init__(self):
        """Initialize the training service with a module-level logger."""
        self.logger = logging.getLogger(__name__)

    def register_losses(self, db: Session, train_loss: float, validation_loss: float, epoch: int, run_id: int):
        """Persist the train and validation loss for one epoch.

        Builds a ``Loss`` row for each split and commits both in a
        single batch so the epoch's metrics are stored atomically.

        Args:
            db (Session): Active SQLAlchemy session.
            train_loss (float): Training loss for the epoch.
            validation_loss (float): Validation loss for the epoch.
            epoch (int): One-based epoch index.
            run_id (int): Primary key of the run these losses belong to.

        Returns:
            list[Loss]: The two persisted loss rows (train then
            validation), refreshed with database-generated values.
        """
        # Save loss
        train_loss_object = Loss(run_id=run_id, epoch=epoch, loss=train_loss, split_type="train")

        validation_loss_object = Loss(run_id=run_id, epoch=epoch, loss=validation_loss, split_type="validation")

        saved_loss = loss_repository.create_many(db=db, losses=[train_loss_object, validation_loss_object])

        return saved_loss

    def perform_training(self, params: TrainParams, class_mapping: dict, run_id: int, progress_callback=None):
        """Execute the full training loop and persist per-epoch losses.

        Builds the model, optimizer, scheduler, datasets, and
        ``Trainer``, then drives the manual epoch loop. Each epoch's
        train and validation losses are persisted via
        :meth:`register_losses`. The ``on_train_start`` / ``on_train_end``
        callbacks are fired around the loop, and early stopping is
        honoured. Opens its own session because this is typically
        invoked on a background thread after the original request has
        returned.

        Args:
            params (TrainParams): Training configuration (hyperparameters,
                dataset paths, device selection, …).
            class_mapping (dict): Mapping from class name to integer
                label, used to build the datasets.
            run_id (int): Primary key of the run these losses belong to.
        """
        db = SessionLocal()
        trainer = None
        try:
            update_training_status(db=db, run_id=run_id, training_status=TrainingStatus.progress)

            device = get_device(
                device=params.device,
                device_index=params.gpu_index if params.device == "cuda" else None,
            )

            # Load model
            model = S3AudioClassifier(
                num_classes=len(class_mapping),
                backbone=params.backbone,
                sample_rate=params.sampling_rate,
                pretrained=params.pretrained,
                freeze_backbone=params.freeze_backbone,
            )
            model.to(device)

            # Load training modules
            optimizer = Adam(params=model.parameters(), lr=params.learning_rate)
            scheduler = ReduceLROnPlateau(optimizer, "min")
            loss_function = nn.CrossEntropyLoss()

            dataset = dataset_repository.get_by_id(db, params.dataset_id)
            if dataset is None:
                raise ValueError(f"Dataset {params.dataset_id} not found")
            s3_prefix = str(dataset.s3_prefix)

            # Create an AudioClassification Dataset reading from S3
            train_file_to_class_mapping = create_file_to_class_mapping_from_s3(
                s3_prefix=s3_prefix, split=params.training_set, bucket="raw-audios"
            )
            train_dataset = S3AudioClassificationDataset(
                file_to_class_mapping=train_file_to_class_mapping,
                sample_rate=params.sampling_rate,
                class_mapping=class_mapping,
                segment_duration=params.segment_duration,
            )

            validation_dataset = None
            if params.validation_set:
                validation_file_to_class_mapping = create_file_to_class_mapping_from_s3(
                    s3_prefix=s3_prefix, split=params.validation_set, bucket="raw-audios"
                )
                # TODO: CHECK if no validationSet is given then the random_split_audio_dataset works as expected with no conflicts for the S3AudioClassificationDataset
                validation_dataset = S3AudioClassificationDataset(
                    file_to_class_mapping=validation_file_to_class_mapping,
                    sample_rate=params.sampling_rate,
                    class_mapping=class_mapping,
                    segment_duration=params.segment_duration,
                )

            # Initialize trainer
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
                # TODO: REMOVE CHECKPOINT PATH?
                path_to_checkpoint=f"{params.checkpoint}.pt",
                device=params.device,
                device_index=params.gpu_index,
            )

            checkpointer = S3Checkpointer(run_id=run_id, checkpoint_name=params.checkpoint, logger=self.logger)

            trainer.callbacks[0] = checkpointer

            self.logger.info("Starting manual training loop...")

            # Fire the "on_train_start" lifecycle hook
            for cb in trainer.callbacks:
                cb.on_train_start(trainer)

            start_time = time.monotonic()
            prev_elapsed = 0.0
            for epoch in range(1, trainer.epochs + 1):
                if trainer.state.early_stop:
                    self.logger.info("Early stopping triggered. Halting training.")
                    break

                # Update the trainer's internal state
                trainer.state.current_epoch = epoch
                train_loss, val_loss = trainer.epoch_step()

                # Save train and validation losses
                _ = self.register_losses(
                    db=db, train_loss=train_loss, validation_loss=val_loss, epoch=epoch, run_id=run_id
                )

                self.logger.info(f"Epoch {epoch} stats: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
                # Write on redis to update progress
                if progress_callback is not None:
                    elapsed = time.monotonic() - start_time
                    last_epoch_time = elapsed - prev_elapsed
                    eta = last_epoch_time * (trainer.epochs - epoch)
                    prev_elapsed = elapsed
                    progress_callback(
                        epoch,
                        trainer.epochs,
                        train_loss,
                        val_loss,
                        trainer.state.lowest_loss,
                        trainer.state.current_patience,
                        params.patience,
                        elapsed,
                        eta,
                    )
            # Fire the "on_train_end" lifecycle hook
            for cb in trainer.callbacks:
                cb.on_train_end(trainer)
        except Exception:
            self.logger.exception("Training failed for run_id=%s", run_id)
            try:
                update_training_status(db=db, run_id=run_id, training_status=TrainingStatus.failure)
            except Exception:
                self.logger.exception("Also failed to mark run_id=%s as failure", run_id)
            raise  # don't swallow                                    # don't swallow
        else:
            # Update training status to success
            update_training_status(db=db, run_id=run_id, training_status=TrainingStatus.success)
            self.logger.info("Training process complete.")
        finally:
            if trainer is not None:  # on_train_end always fires
                for cb in trainer.callbacks:
                    cb.on_train_end(trainer)
            db.close()
