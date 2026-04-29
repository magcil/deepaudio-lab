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
    service = EvaluationService()
    run_id, updated_exp_params = service.update_run_and_exp_params(db, params)

    thread = threading.Thread(
        target=service.perform_evaluation,
        args=(run_id, updated_exp_params),
        daemon=True
    )
    thread.start()

    print("Evaluation has started in a background thread!")

    return {"status": "started", "exp_params": updated_exp_params}
