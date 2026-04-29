# routers/evaluation.py

import threading

import torch
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.evaluation_params import EvaluationOptionsResponse, EvaluationParams
from services.evaluation_service import EvaluationService

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
    """Launch an audio classification evaluation task.

    Accepts evaluation parameters, instantiates a EvaluationService,
    and starts evaluation in a background thread so the request
    returns immediately.

    Args:
        params (EvaluationParams): Evaluation configuration including dataset path,
            model architecture, hyperparameters, and class mapping.

    Returns:
        dict: A status message confirming the training job has started.
    """

    # Perform evaluation
    service = EvaluationService()
    run, _, _ = service.register_run(db, params)

    thread = threading.Thread(target=service.perform_evaluation, args=(params, run.id))
    thread.start()

    print("Evaluation has started in a background thread!")

    return {"status": "started"}
