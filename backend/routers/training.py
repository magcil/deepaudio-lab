# routers/training.py
import json
import threading

import torch
from deepaudiox.modules.pooling import POOLING
from deepaudiox.schemas.types import BackboneName
from fastapi import APIRouter, status

from schemas.train_params import TrainingOptionsResponse, TrainParams
from services.training_service import TrainingService

router = APIRouter(prefix="/train", tags=["Training"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def train(params: TrainParams):
    """Launch an audio classification training task.

    Accepts training parameters, instantiates a TrainingService,
    and starts training in a background thread so the request
    returns immediately.

    Args:
        params (TrainParams): Training configuration including dataset paths,
            model architecture, hyperparameters, and class mapping.

    Returns:
        dict: A status message confirming the training job has started.
    """
    # Load class mapping
    with open(params.class_mapping) as f:
        class_mapping = json.load(f)

    # Perform training
    service = TrainingService()
    thread = threading.Thread(target=service.perform_training, args=(params, class_mapping))
    thread.start()

    print("Training has started in a background thread!")  # Just for confirmation in the console

    return {"status": "started"}


@router.get("/options", response_model=TrainingOptionsResponse, status_code=status.HTTP_200_OK)
def get_training_options():
    """Retrieve available deepaudiox backbones, pooling methods, and GPU indexes.

    Returns:
        dict: Lists containing available backbones, pooling methods, and GPU indexes.
    """
    backbones = list(BackboneName.__args__)
    pooling_methods = list(POOLING.keys())

    gpu_indexes = list(range(torch.cuda.device_count())) if torch.cuda.is_available() else []

    return {"backbones": backbones, "pooling_methods": pooling_methods, "gpu_indexes": gpu_indexes}
