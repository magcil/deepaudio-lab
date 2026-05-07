# services/evaluation_service.py
import logging
import time
from dataclasses import dataclass, field
from typing import cast

import numpy as np
import torch
from deepaudiox import AudioClassifier, audio_classification_dataset_from_dir
from deepaudiox.utils.training_utils import get_device
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader


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
    """Orchestrates the audio classification inference pipeline.

    Responsible for loading the model, running batched inference, and
    computing the classification report. Database persistence is handled
    by the caller (Celery task).
    """

    def __init__(self):
        self.state = EvaluationState()
        self.logger = logging.getLogger(__name__)

    def perform_evaluation(self, exp_params: dict, progress_callback=None) -> dict:
        """Execute the evaluation pipeline and return the classification report.

        Loads the model checkpoint, prepares the evaluation dataset,
        performs batched inference, and computes classification metrics.
        No database interaction occurs here — persistence is the caller's
        responsibility.

        Args:
            exp_params (dict): Experiment parameters required for evaluation
                (checkpoint path, dataset path, batch size, device, etc.).
            progress_callback: Optional callable invoked after each batch with
                (current_batch, total_batches, elapsed, eta).

        Returns:
            dict: Classification report produced by sklearn, keyed by class
                label with precision, recall, f1-score, and support.
        """
        device = get_device(
            device=exp_params["device"],
            device_index=exp_params["gpu_index"] if exp_params["device"] == "cuda" else None,
        )

        model = AudioClassifier.from_checkpoint(f"{exp_params['path_to_checkpoint']}.pt")
        model.to(device)
        model.eval()

        dataset = audio_classification_dataset_from_dir(
            root_dir=exp_params["path_to_test"],
            sample_rate=exp_params["sample_rate"],
            segment_duration=exp_params["segment_duration"],
            class_mapping=exp_params["class_mapping"],
        )

        dataloader = DataLoader(
            dataset,
            batch_size=exp_params["batch_size"],
            shuffle=False,
            num_workers=exp_params["num_workers"],
        )

        total_batches = len(dataloader)
        y_true_batches, y_pred_batches, posterior_batches = [], [], []

        start_time = time.monotonic()
        prev_elapsed = 0.0

        with torch.inference_mode():
            for current_batch, batch in enumerate(dataloader, start=1):
                x = batch["feature"].to(device)
                y_true = batch["y_true"].cpu().numpy()

                inference = model.predict(x)

                y_pred = np.array(inference["y_preds"], dtype=int)
                post = np.array(inference["posteriors"], dtype=float)

                y_true_batches.append(y_true)
                y_pred_batches.append(y_pred)
                posterior_batches.append(post)

                if progress_callback is not None:
                    elapsed = time.monotonic() - start_time
                    batch_time = elapsed - prev_elapsed
                    eta = batch_time * (total_batches - current_batch)
                    prev_elapsed = elapsed
                    progress_callback(current_batch, total_batches, elapsed, eta)

        self.state.y_true = np.concatenate(y_true_batches)
        self.state.y_pred = np.concatenate(y_pred_batches)
        self.state.posteriors = np.concatenate(posterior_batches)

        self.logger.info("Inference complete. Computing classification report.")

        return cast(
            dict,
            classification_report(
                y_true=self.state.y_true,
                y_pred=self.state.y_pred,
                output_dict=True,
            ),
        )
