# routers/evaluation.py

import threading

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.evaluation_params import EvaluationParams
from services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])


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

    thread = threading.Thread(
        target=service.perform_evaluation,
        args=(params, run.id)
    )
    thread.start()

    print("Evaluation has started in a background thread!")

    return {"status": "started"}
