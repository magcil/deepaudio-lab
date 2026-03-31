# services/evaluation_service.py
import logging
from dataclasses import dataclass, field

import numpy as np
import torch
from deepaudiox import AudioClassifier, audio_classification_dataset_from_dir
from deepaudiox.callbacks.reporter import Reporter
from deepaudiox.utils.training_utils import get_device
from torch.utils.data import DataLoader
from tqdm import tqdm

from schemas.evaluation_params import EvaluationParams


@dataclass
class EvaluationState:
    """Stores mutable state tracked throughout the evaluation lifecycle.

    Attributes:
        y_true (np.ndarray): A NumPy array of true labels.
        y_pred (np.ndarray): A NumPy array of predicted labels.
        posteriors (np.ndarray): A NumPy array of posterior probabilities.
    """
    y_true: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))
    y_pred: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))
    posteriors: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))


class EvaluationService:
    """Orchestrates the full audio classification evaluation pipeline."""

    def __init__(self, class_mapping: dict):
        """Initialize the evaluation service with a fresh evaluation state and logger.

        Args:
            class_mapping (dict): Mapping between class names and integers
        """
        self.state = EvaluationState()
        self.class_mapping = class_mapping
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        self.logger = logging.getLogger("ConsoleLogger")

    def perform_evaluation(self, params: EvaluationParams):
        """Execute the full evaluation pipeline.

        Args:
            params (EvaluationParams): Evaluation configuration
        """
        self.device = get_device(device_index=params.gpu_index)
        self.callbacks = [Reporter(logger=self.logger)]

        # Build model
        self.model = AudioClassifier(
            num_classes=len(self.class_mapping),
            backbone=params.backbone,
            sample_rate=params.sampling_rate,
            pretrained=False,
            freeze_backbone=True
        )

        # Load weights
        state_dict = torch.load(params.model_checkpoint)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()


        # Load data
        dataset = audio_classification_dataset_from_dir(
            root_dir=params.evaluation_data,
            sample_rate=params.sampling_rate,
            segment_duration=params.segment_duration,
            class_mapping=self.class_mapping
        )

        dataloader = DataLoader(
            dataset,
            batch_size=params.batch_size,
            shuffle=False,
            num_workers=params.workers
        )

        # Perform evaluation
        y_true_batches, y_pred_batches, posterior_batches = [], [], []
        with tqdm(dataloader, unit="batch", leave=False, desc="Evaluation phase") as tbar:
            for batch in tbar:
                # Move inputs
                x = batch["feature"].to(self.device)
                y_true = batch["y_true"].cpu().numpy()

                # Run model prediction
                inference = self.model.predict(x)
                y_pred = np.array(inference["y_preds"], dtype=int)
                post = np.array(inference["posteriors"], dtype=float)

                # Update lists with new batch results
                y_true_batches.append(y_true)
                y_pred_batches.append(y_pred)
                posterior_batches.append(post)

        # Concatenate all results outside the loop
        self.state.y_true = np.concatenate(y_true_batches)
        self.state.y_pred = np.concatenate(y_pred_batches)
        self.state.posteriors = np.concatenate(posterior_batches)

        # Execute callbacks at the end of evaluation
        for cb in self.callbacks:
            cb.on_testing_end(self)
