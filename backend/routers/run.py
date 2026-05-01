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
            "created_at": run.created_at,
            "parent_run_id": run.parent_run_id,
        }
        for run in runs
    ]


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: int, db: Session = Depends(get_db)):
    """Delete a run and all its owned data.

    Args:
        run_id (int): Primary key of the run to delete.
        db (Session, optional): SQLAlchemy session injected by FastAPI
            via the ``get_db`` dependency.

    Raises:
        EntityNotFoundError: No run with the given ``run_id`` exists.
    """
    deleted = run_repository.delete(db, run_id)
    if not deleted:
        raise EntityNotFoundError("Run", run_id)


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
        "parent_run_id": run.parent_run_id,
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

    if run.train_params:
        tp = run.train_params
        result["train_params"] = {
            "class_mapping": tp.class_mapping,
            "batch_size": tp.batch_size,
            "num_workers": tp.num_workers,
            "epochs": tp.epochs,
            "patience": tp.patience,
            "lr": tp.lr,
            "sample_rate": tp.sample_rate,
            "segment_duration": tp.segment_duration,
            "n_classes": tp.n_classes,
            "backbone": tp.backbone,
            "pretrained_backbone": tp.pretrained_backbone,
            "pooling": tp.pooling,
            "freeze_backbone": tp.freeze_backbone,
            "path_to_checkpoint": tp.path_to_checkpoint,
            "path_to_train": tp.path_to_train,
            "path_to_validation": tp.path_to_validation,
            "device": tp.device,
            "gpu_index": tp.gpu_index,
        }

    if run.evaluation_params:
        ep = run.evaluation_params
        result["evaluation_params"] = {
            "path_to_test": ep.path_to_test,
            "path_to_checkpoint": ep.path_to_checkpoint,
            "class_mapping": ep.class_mapping,
        }

    return result
