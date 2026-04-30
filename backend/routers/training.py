# routers/training.py
import asyncio
import json

import torch
from celery.result import AsyncResult
from deepaudiox import AVAILABLE_BACKBONES, AVAILABLE_POOLING
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from schemas.train_params import TrainingOptionsResponse, TrainParams
from worker.app import celery_app
from worker.training import run_training

router = APIRouter(prefix="/train", tags=["Training"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def train(params: TrainParams):
    with open(params.class_mapping) as f:
        class_mapping = json.load(f)

    task = run_training.delay(params.model_dump(), class_mapping)  # type: ignore[attr-defined]
    return {"task_id": task.id}


@router.get("/options", response_model=TrainingOptionsResponse, status_code=status.HTTP_200_OK)
def get_training_options():
    """Retrieve available deepaudiox backbones, pooling methods, and GPU indexes.

    Returns:
        dict: Lists containing available backbones, pooling methods, and GPU indexes.
    """
    backbones = list(AVAILABLE_BACKBONES)
    pooling_methods = list(AVAILABLE_POOLING)

    gpu_indexes = list(range(torch.cuda.device_count())) if torch.cuda.is_available() else []

    return {"backbones": backbones, "pooling_methods": pooling_methods, "gpu_indexes": gpu_indexes}


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
