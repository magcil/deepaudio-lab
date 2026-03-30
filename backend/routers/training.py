# routers/training.py
import json
import threading

from fastapi import APIRouter, status

from schemas.train_params import TrainParams
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
