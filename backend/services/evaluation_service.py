# services/evaluation_service.py
import logging
from dataclasses import dataclass, field

import numpy as np
import torch
from deepaudiox import AudioClassifier, audio_classification_dataset_from_dir
from deepaudiox.utils.training_utils import get_device
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader

from db.session import SessionLocal
from models.classification_report import ClassificationReport
from repositories import classification_report_repository


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
    """Orchestrates the full audio classification evaluation pipeline.

    Responsible for:
    - validating evaluation requests
    - updating experiment parameters for evaluation
    - running model inference in a separate process/thread
    - storing classification reports
    """

    def __init__(self):
        """Initialize the evaluation service.

        Sets up an empty :class:`EvaluationState` to accumulate predictions
        and configures a simple console logger for progress reporting during
        evaluation.
        """
        self.state = EvaluationState()

        logging.basicConfig(level=logging.INFO, format="%(message)s")
        self.logger = logging.getLogger("ConsoleLogger")

    def perform_evaluation(self, run_id: int, exp_params: dict):
        """Execute the evaluation pipeline for a trained model.

        Loads the model checkpoint, prepares the evaluation dataset,
        performs batched inference, aggregates predictions, computes
        classification metrics, and persists the resulting report.

        This method is designed to run in a background thread and manages
        its own database session lifecycle.

        Args:
            run_id (int): Identifier of the run associated with this evaluation.
            exp_params (dict): Dictionary of experiment parameters required
                for evaluation (e.g., checkpoint path, dataset path, batch size,
                device configuration, and preprocessing settings).

        Raises:
            Exception: Propagates any unexpected errors after rolling back
                the database transaction.
        """
        db = SessionLocal()
        try:
            device = get_device(
                device=exp_params["device"],
                device_index=exp_params["gpu_index"] if exp_params["device"] == "cuda" else None,
            )

            model = AudioClassifier.from_checkpoint(
                f"{exp_params['path_to_checkpoint']}.pt"
            )
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

            y_true_batches, y_pred_batches, posterior_batches = [], [], []

            with torch.inference_mode():
                for batch in dataloader:
                    x = batch["feature"].to(device)
                    y_true = batch["y_true"].cpu().numpy()

                    inference = model.predict(x)

                    y_pred = np.array(inference["y_preds"], dtype=int)
                    post = np.array(inference["posteriors"], dtype=float)

                    y_true_batches.append(y_true)
                    y_pred_batches.append(y_pred)
                    posterior_batches.append(post)

            self.state.y_true = np.concatenate(y_true_batches)
            self.state.y_pred = np.concatenate(y_pred_batches)
            self.state.posteriors = np.concatenate(posterior_batches)

            report = classification_report(
                y_true=self.state.y_true,
                y_pred=self.state.y_pred,
                output_dict=True,
            )

            classification_report_repository.create(
                db=db,
                report=ClassificationReport(
                    run_id=run_id,
                    report=report
                ),
            )

            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
            self.logger.info("Evaluation process complete.")
