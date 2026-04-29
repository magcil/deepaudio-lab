# routers/run.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from exceptions.exceptions import EntityNotFoundError
from repositories import run_repository

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/", status_code=status.HTTP_200_OK)
def get_all_runs(db: Session = Depends(get_db)):
    """Retrieve all runs.

    Args:
        db (Session, optional): SQLAlchemy session injected by FastAPI
            via the ``get_db`` dependency.

    Returns:
        list[dict]: All persisted runs as a list of serialized run objects.
    """
    runs = run_repository.get_all(db)
    return [
        {
            "id": run.id,
            "name": run.name,
            "description": run.description,
            "task_type": run.task_type,
            "created_at": run.created_at
        }
        for run in runs
    ]


@router.get("/{run_id}", status_code=status.HTTP_200_OK)
def get_run(run_id: int, db: Session = Depends(get_db)):
    """Retrieve all information about a single run from all tables.

    Args:
        run_id (int): Primary key of the run to retrieve.
        db (Session, optional): SQLAlchemy session injected by FastAPI
            via the ``get_db`` dependency.

    Raises:
        EntityNotFoundError: No run with the given ``run_id`` exists.

    Returns:
        dict: The run's fields plus its train params or evaluation params,
        loss history, and classification report.
    """
    run = run_repository.get_by_id(db, run_id)
    if run is None:
        raise EntityNotFoundError("Run", run_id)

    result = {
        "id": run.id,
        "name": run.name,
        "description": run.description,
        "task_type": run.task_type,
        "created_at": run.created_at,
        "train_params": None,
        "evaluation_params": None,
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
        exp_params = run.experiment_params
        result["train_params"] = {
            "class_mapping": exp_params.class_mapping,
            "batch_size": exp_params.batch_size,
            "num_workers": exp_params.num_workers,
            "epochs": exp_params.epochs,
            "patience": exp_params.patience,
            "lr": exp_params.lr,
            "sample_rate": exp_params.sample_rate,
            "segment_duration": exp_params.segment_duration,
            "n_classes": exp_params.n_classes,
            "backbone": exp_params.backbone,
            "pretrained_backbone": exp_params.pretrained_backbone,
            "pooling": exp_params.pooling,
            "freeze_backbone": exp_params.freeze_backbone,
            "path_to_checkpoint": exp_params.path_to_checkpoint,
            "path_to_train": exp_params.path_to_train,
            "path_to_validation": exp_params.path_to_validation,
            "path_to_test": exp_params.path_to_test,
            "device": exp_params.device,
            "gpu_index": exp_params.gpu_index,
        }

    return result
