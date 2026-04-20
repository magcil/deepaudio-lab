# services/training_service.py
import json
import logging

import torch.nn as nn
from deepaudiox import AudioClassifier, Trainer, audio_classification_dataset_from_dir
from deepaudiox.utils.training_utils import get_device
from sqlalchemy.orm import Session
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

from exceptions.exceptions import InvalidResourceError, ReferencedEntityNotFoundError, ResourceNotFoundError
from models.run import Run, TaskType
from models.loss import Loss
from models.train_params import TrainParams as TrainParamsModel
from repositories import run_repository, loss_repository
from schemas.train_params import TrainParams
from db.session import SessionLocal


class TrainingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def register_run(
        self, 
        db: Session, 
        params: TrainParams
    ) -> tuple[Run, TrainParamsModel, dict]:
        # --- Validate external resources ---
        try:
            with open(params.class_mapping) as f:
                class_mapping = json.load(f)
        except FileNotFoundError as e:
            raise ResourceNotFoundError("ClassMapping", params.class_mapping) from e
        except json.JSONDecodeError as e:
            raise InvalidResourceError(
                "ClassMapping", params.class_mapping, reason=str(e)
            ) from e

        # --- Validate referenced entities ---
        parent_run_id = None
        if params.parent_run_name is not None:
            parent = run_repository.get_by_name(db, params.parent_run_name)
            if parent is None:
                raise ReferencedEntityNotFoundError("Run", params.parent_run_name)
            parent_run_id = parent.id

        # --- Build entities ---
        run = Run(
            name=params.name,
            description=params.description,
            task_type=TaskType.train,
            parent_run_id=parent_run_id,
        )

        train_params = TrainParamsModel(
            run=run,
            class_mapping=class_mapping,
            batch_size=params.batch_size,
            num_workers=params.workers,
            epochs=params.epochs,
            patience=params.patience,
            lr=params.learning_rate,
            sample_rate=params.sampling_rate,
            segment_duration=params.segment_duration,
            n_classes=params.num_classes,
            backbone=params.backbone,
            pretrained_backbone=params.pretrained,
            pooling=params.pooling,
            freeze_backbone=params.freeze_backbone,
            path_to_checkpoint=params.checkpoint,
            path_to_train=params.training_data,
            path_to_validation=params.validation_data,
            device=params.device,
            gpu_index=params.gpu_index,
        )

        # --- Single transaction: both rows commit together or neither does ---
        created_run, created_train_params = run_repository.create_with_train_params(
            db=db,
            run=run,
            train_params=train_params
        )

        return created_run, created_train_params, class_mapping
    
    def register_losses(
        self, 
        db: Session, 
        train_loss: float, 
        validation_loss: float,
        epoch: int, 
        run_id: int
    ):
        # Save loss
        train_loss_object = Loss(
            run_id = run_id,
            epoch = epoch,
            loss = train_loss,
            split_type = "train"
        )

        validation_loss_object = Loss(
            run_id = run_id,
            epoch = epoch,
            loss = validation_loss,
            split_type = "validation"
        )

        saved_loss = loss_repository.create_many(
            db = db,
            losses = [
                train_loss_object,
                validation_loss_object
            ]
        )

        return saved_loss

    def perform_training(
        self, 
        params: TrainParams,    
        class_mapping: dict,
        run_id: int
    ):
        """Execute the full training pipeline with a manual loop for frontend streaming."""
        db = SessionLocal()
        
        try:
            device = get_device(
                device=params.device,
                device_index=params.gpu_index
            )
            
            # Load model
            model = AudioClassifier(
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

            # Load data
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
                path_to_checkpoint=f"{params.checkpoint}.pt",
                device_index=params.gpu_index,
            )

            self.logger.info("Starting manual training loop...")
            
            # Fire the "on_train_start" lifecycle hook
            for cb in trainer.callbacks:
                cb.on_train_start(trainer)

            # Perform training loop
            try:
                for epoch in range(1, trainer.epochs + 1):
                    if trainer.state.early_stop:
                        self.logger.info("Early stopping triggered. Halting training.")
                        break

                    # Update the trainer's internal state
                    trainer.state.current_epoch = epoch
                    train_loss, val_loss = trainer.epoch_step()

                    # Save train and validation losses
                    _ = self.register_losses(
                        db=db,
                        train_loss=train_loss,
                        validation_loss=val_loss,
                        epoch=epoch,
                        run_id=run_id
                    )

                    self.logger.info(f"Epoch {epoch} stats: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            except Exception:
                self.logger.exception("Training failed for run_id=%s", run_id)
                raise
            finally:
                # Fire the "on_train_end" lifecycle hook
                for cb in trainer.callbacks:
                    cb.on_train_end(trainer)        
        finally:
            db.close()
            self.logger.info("Training process complete.")


