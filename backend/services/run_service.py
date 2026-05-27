# services/run_service.py


from sqlalchemy.orm import Session

from adapters.utils import get_class_mapping_from_s3_dataset
from exceptions.exceptions import (
    EntityNotFoundError,
    InvalidStateError,
    ReferencedEntityNotFoundError,
)
from models.experiment_params import ExperimentParams
from models.run import EvaluationStatus, Run, TaskType
from repositories import dataset_repository, experiment_params_repository, run_repository
from schemas.evaluation_params import EvaluationParams
from schemas.train_params import TrainParams


def get_all(db: Session) -> list[dict]:
    """Retrieve all runs
    Args:
        db (Session): SQLAlchemy database session.
    Returns:
        list[dict]: Serialized list of runs.
    """
    runs = run_repository.get_all(db)
    return [_serialize_run(run) for run in runs]


def get(db: Session, **filters) -> list[dict]:
    """Retrieve runs filtered by dynamic Run fields.

    Args:
        db (Session): SQLAlchemy database session.
        **filters: Dynamic Run field/value filters. ``None`` values are ignored.

    Returns:
        list[dict]: Serialized list of matching runs.
    """
    runs = run_repository.get_query(db, **filters)
    return [_serialize_run(run) for run in runs]


def get_by_id(db: Session, run_id: int) -> dict | None:
    """Retrieve a single run with full details.

    Args:
        db (Session): SQLAlchemy database session.
        run_id (int): Primary key of the run to retrieve.

    Returns:
        dict | None: Serialized run detail, or None if not found.
    """
    run = run_repository.get_by_id(db, run_id)
    if run is None:
        return None
    return _serialize_run_detail(run)


def register_train(db: Session, params: TrainParams) -> dict:
    """Validate inputs and persist a new training run with its experiment parameters.

    Loads and parses the class-mapping file, constructs a new ``Run`` and
    its associated ``ExperimentParams``, and commits both atomically to the
    database.

    Args:
        db (Session): Active SQLAlchemy session.
        params (TrainParams): Training configuration submitted by the client,
            including model settings, hyperparameters, and dataset paths.

    Raises:
        ResourceNotFoundError: If the class-mapping file does not exist at
            the path specified in ``params.class_mapping``.
        InvalidResourceError: If the class-mapping file exists but cannot
            be parsed as valid JSON.

    Returns:
        dict: Serialized run detail including the new run's metadata and
            its persisted experiment parameters.
    """
    dataset = dataset_repository.get_by_id(db, params.dataset_id)
    if dataset is None:
        raise EntityNotFoundError("Dataset", params.dataset_id)

    class_mapping = get_class_mapping_from_s3_dataset(
        s3_prefix=dataset.s3_prefix, split=params.training_set, bucket="raw-audios"
    )

    run = Run(name=params.experiment_name, description=params.description, task_type=TaskType.train)
    exp_params = ExperimentParams(
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
        dataset_id=params.dataset_id,
        path_to_train=params.training_set,
        path_to_validation=params.validation_set,
        device=params.device,
        gpu_index=params.gpu_index,
    )

    created_run = run_repository.create_run_with_params(db=db, run=run, exp_params=exp_params)
    return _serialize_run_detail(created_run)


def register_evaluation(db: Session, evaluation_params: EvaluationParams):
    """Validate and update run and experiment parameters for evaluation.

    Retrieves the training run referenced in the evaluation request,
    ensures it exists and has not already been evaluated, updates the
    run's task type, and sets the test dataset path in the associated
    experiment parameters. Both updates are committed atomically via a
    dedicated repository method.

    Args:
        db (Session): Active SQLAlchemy session.
        evaluation_params (EvaluationParams): User-provided evaluation
            configuration containing the training run name and test data path.

    Raises:
        ReferencedEntityNotFoundError: If the referenced training run
            does not exist.
        InvalidStateError: If the experiment has already been evaluated
            (i.e., ``path_to_test`` is already set).

    Returns:
        tuple[int, dict]: The ID of the training run and a dictionary
            representation of the updated experiment parameters.
    """
    # Validate referenced train experiment
    train_exp = run_repository.get_by_name(db, evaluation_params.train_name)
    if train_exp is None:
        raise ReferencedEntityNotFoundError("Run", evaluation_params.train_name)

    if train_exp.has_evaluation:
        raise InvalidStateError("Experiment already evaluated")

    # Update run fields
    train_exp.task_type = TaskType.train_evaluation
    train_exp.evaluation_status = EvaluationStatus.pending
    run_repository.update_run(db=db, run=train_exp)

    # Update experiment params
    exp_params = train_exp.experiment_params

    exp_params.path_to_test = evaluation_params.evaluation_data
    experiment_params_repository.update_experiment_params(db=db, exp_params=exp_params)

    # TODO: RENAME PATH VARIABLES?
    exp_params_dict = {
        "dataset_id": exp_params.dataset_id,
        "path_to_checkpoint": exp_params.path_to_checkpoint,
        "path_to_test": exp_params.path_to_test,
        "sample_rate": exp_params.sample_rate,
        "segment_duration": exp_params.segment_duration,
        "class_mapping": exp_params.class_mapping,
        "batch_size": exp_params.batch_size,
        "num_workers": exp_params.num_workers,
        "device": exp_params.device,
        "gpu_index": exp_params.gpu_index,
    }

    return train_exp.id, exp_params_dict


def _serialize_run(run) -> dict:
    """Serialize a Run ORM object into a base dictionary representation.

    Extracts only the core identifying fields of the run, without any
    related entities. Used as the base for ``_serialize_run_detail``.

    Args:
        run (Run): SQLAlchemy Run ORM object.

    Returns:
        dict: Dictionary containing the run's id, name, description,
            task_type, and created_at timestamp.
    """
    return {
        "id": run.id,
        "name": run.name,
        "description": run.description,
        "task_type": run.task_type,
        "has_evaluation": run.has_evaluation,
        "created_at": run.created_at,
    }


def _serialize_run_detail(run) -> dict:
    """Serialize a Run ORM object into a detailed dictionary representation.

    Extends the base run serialization with experiment parameters, per-epoch
    loss history, and classification report. Experiment parameters are included
    only if the run has an associated ``ExperimentParams`` row.

    Args:
        run (Run): SQLAlchemy Run ORM object, with ``losses``,
            ``experiment_params``, and ``classification_report``
            relationships loaded.

    Returns:
        dict: Dictionary containing the run's base fields (id, name,
            description, task_type, created_at), experiment parameters
            or ``None`` if not present, a list of loss records keyed by
            epoch and split type, and the classification report or ``None``
            if not yet evaluated.
    """
    result = {
        **_serialize_run(run),
        "exp_params": None,
        "losses": [
            {
                "epoch": loss.epoch,
                "split_type": loss.split_type,
                "loss": loss.loss,
            }
            for loss in run.losses
        ],
        "classification_report": (run.classification_report.report if run.classification_report else None),
    }
    if run.experiment_params:
        exp = run.experiment_params
        result["exp_params"] = {
            "class_mapping": exp.class_mapping,
            "batch_size": exp.batch_size,
            "num_workers": exp.num_workers,
            "epochs": exp.epochs,
            "patience": exp.patience,
            "lr": exp.lr,
            "sample_rate": exp.sample_rate,
            "segment_duration": exp.segment_duration,
            "n_classes": exp.n_classes,
            "backbone": exp.backbone,
            "pretrained_backbone": exp.pretrained_backbone,
            "pooling": exp.pooling,
            "freeze_backbone": exp.freeze_backbone,
            "path_to_checkpoint": exp.path_to_checkpoint,
            "dataset_id": exp.dataset_id,
            "path_to_train": exp.path_to_train,
            "path_to_validation": exp.path_to_validation,
            "path_to_test": exp.path_to_test,
            "device": exp.device,
            "gpu_index": exp.gpu_index,
        }
    return result
