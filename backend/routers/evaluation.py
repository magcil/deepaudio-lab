# routers/evaluation.py
import json
import threading

from fastapi import APIRouter, status

from schemas.evaluation_params import EvaluationParams
from services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def evaluate(params: EvaluationParams):
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

    # Load class mapping
    with open(params.class_mapping) as f:
        class_mapping = json.load(f)

    # Perform evaluation
    service = EvaluationService(class_mapping=class_mapping)
    thread = threading.Thread(target=service.perform_evaluation, args=(params,))
    thread.start()

    print("Evaluation has started in a background thread!") 

    return {"status": params}
