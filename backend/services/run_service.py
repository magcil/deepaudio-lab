# services/run_service.py

from sqlalchemy.orm import Session

from adapters.utils import get_class_mapping_from_s3_dataset
from config.limits import MAX_BATCH_SIZE, MAX_EPOCHS, MAX_NUM_WORKERS, MAX_SEGMENT_DURATION
from exceptions.exceptions import (
    EntityNotFoundError,
    InvalidStateError,
    ReferencedEntityNotFoundError,
    UnprocessableEntityError,
)
from models.experiment_params import ExperimentParams
from models.run import EvaluationStatus, Run, TaskType
from repositories import dataset_repository, experiment_params_repository, run_repository
from schemas.evaluation_params import EvaluationParams
from schemas.train_params import TrainParams
from storage.client import ARTIFACTS_BUCKET, CHECKPOINTS_BUCKET
from storage.filer import delete_prefix


def get_all(db: Session, owner_id: str | None = None) -> list[dict]:
    """Retrieve all runs, optionally scoped to a specific owner.

    Args:
        db (Session): SQLAlchemy database session.
        owner_id (str | None): If provided, only returns runs created by
            this user. If None, returns runs for all users.

    Returns:
        list[dict]: Serialized list of all matching runs.
    """
    runs = run_repository.get_all(db, owner_id=owner_id)
    return [_serialize_run(run) for run in runs]


def get(db: Session, owner_id: str | None = None, **filters) -> list[dict]:
    """Retrieve runs filtered by dynamic Run fields.

    Args:
        db (Session): SQLAlchemy database session.
        owner_id (str | None): If provided, only returns runs created by
            this user. If None, returns runs for all users.
        **filters: Dynamic Run field/value filters. ``None`` values are ignored.

    Returns:
        list[dict]: Serialized list of matching runs.
    """
    runs = run_repository.get_query(db, created_by=owner_id, **filters)
    return [_serialize_run(run) for run in runs]


def get_by_id(db: Session, run_id: int, owner_id: str | None = None) -> dict | None:
    """Retrieve a single run with full details.

    Args:
        db (Session): SQLAlchemy database session.
        run_id (int): Primary key of the run to retrieve.
        owner_id (str | None): If provided, scopes the lookup to runs owned
            by this user. If None, searches across all users.

    Returns:
        dict | None: Serialized run detail, or None if not found.
    """
    run = run_repository.get_by_id(db, run_id, owner_id=owner_id)
    if run is None:
        return None
    return _serialize_run_detail(run, db)


def delete(db: Session, run_id: int, owner_id: str | None = None) -> bool:
    """Delete a run and its S3 checkpoint.

    Attempts to delete the checkpoint from SeaweedFS before removing the
    DB row. S3 errors are swallowed so a missing or never-uploaded
    checkpoint does not block the deletion.

    Args:
        db (Session): SQLAlchemy database session.
        run_id (int): Primary key of the run to delete.
        owner_id (str | None): If provided, scopes the deletion to runs
            owned by this user.

    Returns:
        bool: True if a run was deleted, False if not found.
    """
    run = run_repository.get_by_id(db, run_id, owner_id=owner_id)
    if run is None:
        return False

    if run.experiment_params and run.experiment_params.path_to_checkpoint:
        try:
            delete_prefix(bucket=CHECKPOINTS_BUCKET, prefix=f"run_{run_id}/")
        except Exception:
            pass

    if run.deploy_artifact_key:
        try:
            delete_prefix(bucket=ARTIFACTS_BUCKET, prefix=f"run_{run_id}/")
        except Exception:
            pass

    return run_repository.delete(db, run_id)


def validate_run_params(params: TrainParams):
    errors = []

    if params.batch_size > MAX_BATCH_SIZE:
        errors.append(f"batch_size must be <= {MAX_BATCH_SIZE}")

    if params.epochs > MAX_EPOCHS:
        errors.append(f"epochs must be <= {MAX_EPOCHS}")

    if params.segment_duration > MAX_SEGMENT_DURATION:
        errors.append(f"segment_duration must be <= {MAX_SEGMENT_DURATION}")

    if params.workers > MAX_NUM_WORKERS:
        errors.append(f"workers must be <= {MAX_NUM_WORKERS}")

    if errors:
        raise UnprocessableEntityError(f"Parameters exceed limits: {', '.join(errors)}")


def register_train(db: Session, params: TrainParams, owner_id: str) -> dict:
    """Validate inputs and persist a new training run with its experiment parameters.

    Args:
        db (Session): Active SQLAlchemy session.
        params (TrainParams): Training configuration submitted by the client.
        owner_id (str): Keycloak subject ID of the user creating the run.

    Returns:
        dict: Serialized run detail including the new run's metadata and
            its persisted experiment parameters.
    """
    validate_run_params(params=params)

    dataset = dataset_repository.get_by_id(db, params.dataset_id)
    if dataset is None:
        raise EntityNotFoundError("Dataset", params.dataset_id)

    class_mapping = get_class_mapping_from_s3_dataset(
        s3_prefix=dataset.s3_prefix, split=params.training_set, bucket="raw-audios"
    )

    run = Run(
        created_by=owner_id,
        name=params.experiment_name,
        description=params.description,
        task_type=TaskType.train,
    )
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
        n_classes=len(class_mapping),
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
    return _serialize_run_detail(created_run, db)


def register_evaluation(db: Session, evaluation_params: EvaluationParams, owner_id: str):
    """Validate and update run and experiment parameters for evaluation.

    Args:
        db (Session): Active SQLAlchemy session.
        evaluation_params (EvaluationParams): User-provided evaluation configuration.
        owner_id (str): Keycloak subject ID of the user requesting evaluation.

    Raises:
        ReferencedEntityNotFoundError: If the referenced training run does not exist
            or does not belong to the requesting user.
        InvalidStateError: If the experiment has already been evaluated.

    Returns:
        tuple[int, dict]: The ID of the training run and the updated experiment parameters.
    """
    train_exp = run_repository.get_by_id(db, evaluation_params.train_run_id, owner_id=owner_id)
    if train_exp is None:
        raise ReferencedEntityNotFoundError("Run", evaluation_params.train_run_id)

    if train_exp.has_evaluation:
        raise InvalidStateError("Experiment already evaluated")

    train_exp.task_type = TaskType.train_evaluation
    train_exp.evaluation_status = EvaluationStatus.pending
    run_repository.update_run(db=db, run=train_exp)

    exp_params = train_exp.experiment_params
    exp_params.path_to_test = evaluation_params.test_set
    experiment_params_repository.update_experiment_params(db=db, exp_params=exp_params)

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
    dataset_id = run.experiment_params.dataset_id if run.experiment_params else None
    return {
        "id": run.id,
        "name": run.name,
        "description": run.description,
        "task_type": run.task_type,
        "has_evaluation": run.has_evaluation,
        "created_at": run.created_at,
        "dataset_id": dataset_id,
        "training_status": run.training_status,
        "deploy_name": run.deploy_name,
        "deploy_artifact_key": run.deploy_artifact_key,
    }


def _serialize_run_detail(run, db: Session) -> dict:
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
        dataset = dataset_repository.get_by_id(db, exp.dataset_id)
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
            "dataset_name": dataset.name if dataset else None,
            "path_to_train": exp.path_to_train,
            "path_to_validation": exp.path_to_validation,
            "path_to_test": exp.path_to_test,
            "device": exp.device,
            "gpu_index": exp.gpu_index,
        }
    return result
