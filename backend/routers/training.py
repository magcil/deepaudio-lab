# routers/training.py

import torch
from deepaudiox import AVAILABLE_BACKBONES, AVAILABLE_POOLING
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.train_params import TrainingOptionsResponse, TrainParams
from services.training_service import TrainingService

router = APIRouter(prefix="/train", tags=["Training"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def train(params: TrainParams, db: Session = Depends(get_db)):
    """Launch an audio classification training task."""
    service = TrainingService()
    run, train_params, class_mapping = service.register_run(db, params)

    # thread = threading.Thread(
    #     target=service.perform_training,
    #     args=(params, class_mapping)
    # )
    # thread.start()

    return {
        "status": "started", 
        "run_name": run.name, 
        "train_params": train_params
    }


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
