# routers/training.py
import asyncio
import json

import torch
from celery.result import AsyncResult
from deepaudiox import AVAILABLE_BACKBONES, AVAILABLE_POOLING
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from auth.service import get_current_user, require_regular
from db.session import get_db
from repositories import run_repository
from schemas.train_params import TrainingOptionsResponse, TrainParams
from schemas.user_info import UserInfo
from services import concurrency_service, limit_service, run_service
from worker.app import celery_app
from worker.training import run_training

router = APIRouter(prefix="/train", tags=["Training"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def train(params: TrainParams, db: Session = Depends(get_db), user: UserInfo = Depends(require_regular)):
    """Start a training run asynchronously.

    Registers the run and its training parameters in the database, then
    kicks off the actual training loop on a background thread so the
    request returns immediately with ``202 Accepted``.

    Args:
        params (TrainParams): Training configuration submitted by the
            client (model/backbone choice, dataset, hyperparameters, …).
        db (Session, optional): SQLAlchemy session injected by FastAPI
            via the ``get_db`` dependency.

    Returns:
        dict: Acknowledgement payload with the run status, the assigned
        run name, and the persisted training parameters.
    """
    # Admission control: reject (429/503) if the user or system is at its job cap.
    concurrency_service.check_can_start_training(db, user.sub)

    run_detail = run_service.register_train(db, params, owner_id=user.sub)
    run_id = run_detail["id"]
    class_mapping = run_detail["exp_params"]["class_mapping"]
    task = run_training.delay(params.model_dump(), class_mapping, run_id, user.sub)
    run_repository.update_task_id(db, run_id, task.id)
    return {"task_id": task.id}


@router.get("/options", response_model=TrainingOptionsResponse, status_code=status.HTTP_200_OK)
def get_training_options(_: UserInfo = Depends(get_current_user)):
    """Retrieve available deepaudiox backbones, pooling methods, and GPU indexes.

    Returns:
        dict: Lists containing available backbones, pooling methods, and GPU indexes.
    """
    backbones = list(AVAILABLE_BACKBONES)
    pooling_methods = list(AVAILABLE_POOLING)

    cuda_available = torch.cuda.is_available()
    mps_available = torch.backends.mps.is_available()
    gpu_indexes = list(range(torch.cuda.device_count())) if cuda_available else []

    return {
        "backbones": backbones,
        "pooling_methods": pooling_methods,
        "gpu_indexes": gpu_indexes,
        "cuda_available": cuda_available,
        "mps_available": mps_available,
    }


@router.get("/progress/{task_id}")
async def get_progress(task_id: str, db: Session = Depends(get_db), user: UserInfo = Depends(get_current_user)):
    """Stream training progress updates via Server-Sent Events.

    Polls the Celery task state every 2 seconds and streams updates until
    the task reaches a terminal state (SUCCESS, FAILURE, REVOKED). Regular
    users can only access their own tasks; admins can access any task.

    Args:
        task_id (str): Celery task UUID returned by the train endpoint.
        db (Session): SQLAlchemy database session.
        user (UserInfo): The authenticated user resolved by `get_current_user`.

    Raises:
        HTTPException 403: If a non-admin user tries to access a task that
            does not belong to them.

    Returns:
        StreamingResponse: SSE stream of task state and progress metadata.
    """
    if not user.is_admin:
        run = run_repository.get_by_task_id(db, task_id)
        if run is None or run.created_by != user.sub:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def event_stream():
        while True:
            result = AsyncResult(task_id, app=celery_app)
            info = result.info
            if isinstance(info, Exception):
                info = {"error": str(info)}
            yield f"data: {json.dumps({'state': result.state, 'info': info})}\n\n"
            if result.state in ("SUCCESS", "FAILURE", "REVOKED"):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/limits", status_code=status.HTTP_200_OK)
def get_training_limits(_: UserInfo = Depends(get_current_user)):
    return limit_service.get_current_limits()
