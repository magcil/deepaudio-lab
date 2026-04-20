# services/evaluation_service.py
import json
import logging
from dataclasses import dataclass, field

import numpy as np
import torch
from deepaudiox import AudioClassifier, audio_classification_dataset_from_dir
from deepaudiox.callbacks.reporter import Reporter
from deepaudiox.utils.training_utils import get_device
from sklearn.metrics import classification_report
from sqlalchemy.orm import Session
from torch.utils.data import DataLoader
from tqdm import tqdm

from db.session import SessionLocal
from exceptions.exceptions import InvalidResourceError, ReferencedEntityNotFoundError, ResourceNotFoundError
from models.classification_report import ClassificationReport
from models.evaluation_params import EvaluationParams as EvaluationParamsModel
from models.run import Run, TaskType
from repositories import classification_report_repository, run_repository
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

    def __init__(self):
        """Initialize the evaluation service with a fresh evaluation state and logger.

        Args:
            class_mapping (dict): Mapping between class names and integers
        """
        self.state = EvaluationState()
        self.class_mapping = {}
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        self.logger = logging.getLogger("ConsoleLogger")

    def register_run(
        self, db: Session, params: EvaluationParams
    ) -> tuple[Run, EvaluationParams, dict]:
        """Validate inputs and persist a new evaluation run.

        Loads and parses the class-mapping file, resolves the optional
        parent run by name, then writes the ``Run`` and its
        ``EvaluationParams`` row atomically. The parsed class mapping is
        cached on ``self`` so later calls to :meth:`perform_evaluation`
        reuse it.

        Args:
            db (Session): Active SQLAlchemy session.
            params (EvaluationParams): Evaluation configuration submitted
                by the client.

        Raises:
            ResourceNotFoundError: The class-mapping file does not exist.
            InvalidResourceError: The class-mapping file exists but could
                not be parsed as JSON.
            ReferencedEntityNotFoundError: ``params.parent_run_name`` is
                set but no run with that name exists.

        Returns:
            tuple[Run, EvaluationParams, dict]: The persisted run, the
            persisted evaluation-params row, and the loaded class mapping.
        """
        # Validate external resources
        try:
            with open(params.class_mapping) as f:
                class_mapping = json.load(f)
        except FileNotFoundError as e:
            raise ResourceNotFoundError("ClassMapping", params.class_mapping) from e
        except json.JSONDecodeError as e:
            raise InvalidResourceError(
                "ClassMapping", params.class_mapping, reason=str(e)
            ) from e
        
        self.class_mapping = class_mapping

        # Validate referenced entities
        parent_run_id = None
        if params.parent_run_name is not None:
            parent = run_repository.get_by_name(db, params.parent_run_name)
            if parent is None:
                raise ReferencedEntityNotFoundError("Run", params.parent_run_name)
            parent_run_id = parent.id

        # Build entities
        run = Run(
            name=params.name,
            description=params.description,
            task_type=TaskType.evaluation,
            parent_run_id=parent_run_id,
        )

        evaluation_params = EvaluationParamsModel(
            run=run, 
            path_to_test=params.evaluation_data,
            path_to_checkpoint=params.model_checkpoint,
            class_mapping=class_mapping,
        )
        # Single transaction: both rows commit together or neither does
        created_run, created_evaluation_params = run_repository.create_with_evaluation_params(
            db=db,
            run=run,
            evaluation_params=evaluation_params
        )

        return created_run, created_evaluation_params, class_mapping
    

    def perform_evaluation(
        self,
        params: EvaluationParams,
        run_id: int
    ):
        """Execute the full evaluation pipeline and persist the report.

        Loads the checkpoint, runs inference in batches over the
        evaluation dataset, fires the ``on_testing_end`` callback hook,
        computes a sklearn classification report, and stores it against
        the given run. Opens its own session because this is typically
        invoked on a background thread after the original request has
        returned.

        Args:
            params (EvaluationParams): Evaluation configuration (paths,
                sampling rate, batch size, worker count, GPU index, …).
            run_id (int): Primary key of the run this evaluation belongs
                to. Used to attach the classification report.
        """
        db = SessionLocal()
        try:
            self.device = get_device(device_index=params.gpu_index)
            self.callbacks = [Reporter(logger=self.logger)]

            # Build model / Load from checkpoint (deepaudio-x >= v0.4.2)
            self.model = AudioClassifier.from_checkpoint(f"{params.model_checkpoint}.pt")
            self.model.to(self.device)
            self.model.eval()

            # Load data
            dataset = audio_classification_dataset_from_dir(
                root_dir=params.evaluation_data,
                sample_rate=params.sampling_rate,
                segment_duration=params.segment_duration,
                class_mapping=self.class_mapping,
            )

            dataloader = DataLoader(dataset, batch_size=params.batch_size, shuffle=False, num_workers=params.workers)

            # Perform evaluation
            y_true_batches, y_pred_batches, posterior_batches = [], [], []
            try:
                with torch.inference_mode(), tqdm(
                    dataloader, unit="batch", leave=False, desc="Evaluation phase"
                ) as tbar:
                    for batch in tbar:
                        x = batch["feature"].to(self.device)
                        y_true = batch["y_true"].cpu().numpy()

                        inference = self.model.predict(x)
                        y_pred = np.array(inference["y_preds"], dtype=int)
                        post = np.array(inference["posteriors"], dtype=float)

                        y_true_batches.append(y_true)
                        y_pred_batches.append(y_pred)
                        posterior_batches.append(post)
            except Exception:
                self.logger.exception("Evaluation failed for run_id=%s", run_id)
                raise

            # Aggregate results
            self.state.y_true = np.concatenate(y_true_batches)
            self.state.y_pred = np.concatenate(y_pred_batches)
            self.state.posteriors = np.concatenate(posterior_batches)

            # Fire the on_testing_end lifecycle hook after state is populated
            for cb in self.callbacks:
                cb.on_testing_end(self)

            report = classification_report(
                y_true=self.state.y_true,
                y_pred=self.state.y_pred,
                output_dict=True,
            )
            classification_report_repository.create(
                db=db,
                report=ClassificationReport(run_id=run_id, report=report)
            )
        finally:
            db.close()
            self.logger.info("Evaluation process complete.")

