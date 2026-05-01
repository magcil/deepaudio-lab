# routers/training.py
import asyncio
import json
from typing import cast

import torch
from celery.result import AsyncResult
from deepaudiox import AVAILABLE_BACKBONES, AVAILABLE_POOLING
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.session import get_db
from repositories import run_repository
from schemas.train_params import TrainingOptionsResponse, TrainParams
from services.training_service import TrainingService
from worker.app import celery_app
from worker.training import run_training

router = APIRouter(prefix="/train", tags=["Training"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def train(params: TrainParams, db: Session = Depends(get_db)):
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
    service = TrainingService()
    run, _, class_mapping = service.register_run(db, params)
    task = run_training.delay(params.model_dump(), class_mapping, cast(int, run.id))
    run_repository.update_task_id(db, cast(int, run.id), task.id)

    return {"task_id": task.id}


@router.get("/options", response_model=TrainingOptionsResponse, status_code=status.HTTP_200_OK)
def get_training_options():
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
async def get_progress(task_id: str):
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
