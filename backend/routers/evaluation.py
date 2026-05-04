# routers/evaluation.py

import threading

import torch
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.evaluation_params import EvaluationOptionsResponse, EvaluationParams
from services import run_service
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
    """Start an audio classification evaluation job.

    Validates the requested training run, updates its associated
    experiment parameters with the evaluation dataset, and launches
    the evaluation pipeline in a background thread. The request
    returns immediately while evaluation continues asynchronously.

    Args:
        params (EvaluationParams): Evaluation configuration including
            the name of the training run to evaluate and the path to
            the evaluation dataset.
        db (Session): Active SQLAlchemy session provided by FastAPI.

    Returns:
        dict: A response indicating that evaluation has started,
            including the run ID and updated experiment parameters.

    Raises:
        ReferencedEntityNotFoundError: If the specified training run
            does not exist.
        InvalidStateError: If the experiment has already been evaluated.
    """

    # Perform evaluation
    run_id, exp_params = run_service.register_evaluation(db, params)
    
    evaluation_service = EvaluationService()
    thread = threading.Thread(
        target=evaluation_service.perform_evaluation,
        args=(run_id, exp_params),
        daemon=True
    )
    thread.start()
    return {"status": "started", "run_id": run_id}