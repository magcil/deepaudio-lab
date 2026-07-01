# services/evaluation_service.py
import gc
import logging
import time
from dataclasses import dataclass, field
from typing import cast

import numpy as np
import torch
from deepaudiox.utils.training_utils import get_device
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader

from adapters.classifiers import S3AudioClassifier
from adapters.dataset import S3AudioClassificationDataset
from adapters.utils import create_file_to_class_mapping_from_s3
from db.session import SessionLocal
from exceptions.exceptions import ReferencedEntityNotFoundError
from models.run import EvaluationStatus, TaskType
from repositories import dataset_repository, run_repository
from repositories.run_repository import update_evaluation_status


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

    def perform_evaluation(self, run_id: int, exp_params: dict, user_id: str, progress_callback=None):
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
        db = SessionLocal()
        # Pre-bound so the finally block can unconditionally `del` them to free
        # GPU memory, even if an exception fires before they are assigned.
        model = None
        x = None
        try:
            device = get_device(
                device=exp_params["device"],
                device_index=exp_params["gpu_index"] if exp_params["device"] == "cuda" else None,
            )

            update_evaluation_status(db=db, run_id=run_id, evaluation_status=EvaluationStatus.progress)

            model = S3AudioClassifier.from_checkpoint(
                path=f"run_{run_id}/{user_id}/{exp_params.get('path_to_checkpoint')}.pt"
            )
            model.to(device)
            model.eval()

            class_mapping = exp_params["class_mapping"]

            dataset_record = dataset_repository.get_by_id(db, exp_params["dataset_id"])
            if dataset_record is None:
                raise ValueError(f"Dataset {exp_params['dataset_id']} not found")

            test_file_to_class_mapping = create_file_to_class_mapping_from_s3(
                s3_prefix=str(dataset_record.s3_prefix),
                split=exp_params["path_to_test"],
                bucket="raw-audios",
            )
            dataset = S3AudioClassificationDataset(
                file_to_class_mapping=test_file_to_class_mapping,
                sample_rate=exp_params.get("sample_rate"),
                class_mapping=class_mapping,
                segment_duration=exp_params.get("segment_duration"),
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

        except Exception:
            self.logger.info("Inference failed.")

            # Update run fields after failure
            train_exp = run_repository.get_by_id(db, run_id)
            if train_exp is None:
                raise ReferencedEntityNotFoundError("Run", run_id) from None

            train_exp.task_type = TaskType.train
            train_exp.evaluation_status = EvaluationStatus.failure
            train_exp.has_evaluation = False

            run_repository.update_run(db=db, run=train_exp)

        else:
            self.logger.info("Inference complete. Computing classification report.")
            update_evaluation_status(db=db, run_id=run_id, evaluation_status=EvaluationStatus.success)

            # Update run fields after success - set hasEvaluation to True
            train_exp = run_repository.get_by_id(db, run_id)
            if train_exp is None:
                raise ReferencedEntityNotFoundError("Run", run_id) from None

            train_exp.has_evaluation = True

            run_repository.update_run(db=db, run=train_exp)

            class_mapping = exp_params["class_mapping"]  # {name: index}
            index_to_name = {v: k for k, v in class_mapping.items()}
            target_names = [index_to_name[i] for i in range(len(class_mapping))]

            return cast(
                dict,
                classification_report(
                    y_true=self.state.y_true, y_pred=self.state.y_pred, output_dict=True, target_names=target_names
                ),
            )
        finally:
            # Release GPU memory held by this job so it doesn't linger in the
            # long-lived (--pool=solo) worker process and starve the next run.
            # empty_cache() only frees UNreferenced memory, so drop refs first.
            del model, x
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            db.close()
