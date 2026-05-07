# routers/evaluation.py
import asyncio
import json

import torch
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db.session import get_db
from repositories import run_repository
from schemas.evaluation_params import EvaluationOptionsResponse, EvaluationParams
from services import run_service
from worker.app import celery_app
from worker.evaluation import run_evaluation

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])


@router.get("/options", response_model=EvaluationOptionsResponse, status_code=status.HTTP_200_OK)
def get_evaluation_options():
    """Retrieve available device options for evaluation.

    Returns:
        dict: GPU indexes and availability flags for CUDA and MPS devices.
    """
    cuda_available = torch.cuda.is_available()
    mps_available = torch.backends.mps.is_available()
    gpu_indexes = list(range(torch.cuda.device_count())) if cuda_available else []

    return {
        "gpu_indexes": gpu_indexes,
        "cuda_available": cuda_available,
        "mps_available": mps_available,
    }


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def evaluate(params: EvaluationParams, db: Session = Depends(get_db)):
    """Start an audio classification evaluation job.

    Validates the requested training run, updates its associated
    experiment parameters with the evaluation dataset, and dispatches
    the evaluation pipeline as a Celery task. The request returns
    immediately while evaluation continues asynchronously.

    Args:
        params (EvaluationParams): Evaluation configuration including
            the name of the training run to evaluate and the path to
            the evaluation dataset.
        db (Session): Active SQLAlchemy session provided by FastAPI.

    Returns:
        dict: A response containing the Celery task ID.

    Raises:
        ReferencedEntityNotFoundError: If the specified training run
            does not exist.
        InvalidStateError: If the experiment has already been evaluated.
    """
    run_id, exp_params = run_service.register_evaluation(db, params)
    task = run_evaluation.delay(run_id, exp_params)
    run_repository.update_task_id(db, run_id, task.id)
    return {"task_id": task.id}


@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """Stream evaluation progress updates via Server-Sent Events.

    Polls the Celery task state every 2 seconds and streams updates
    until the task reaches a terminal state (SUCCESS, FAILURE, REVOKED).

    Args:
        task_id (str): Celery task UUID returned by the evaluate endpoint.

    Returns:
        StreamingResponse: SSE stream of task state and progress metadata.
    """

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
