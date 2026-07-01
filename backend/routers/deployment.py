from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from auth.service import get_current_user
from db.session import get_db
from exceptions.exceptions import EntityNotFoundError, InvalidStateError
from models.run import TrainingStatus
from repositories import run_repository
from repositories.run_repository import update_deploy_task_id
from schemas.deploy_request import DeployRequest
from schemas.user_info import UserInfo
from services.deployment_service import generate_download_url
from worker.deployment import run_deployment

router = APIRouter(prefix="/runs", tags=["Deployment"])


@router.post(
    "/{run_id}/deploy",
    status_code=status.HTTP_202_ACCEPTED,
)
def create_bundle(
    run_id: int,
    request: DeployRequest,
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    """Dispatch a Celery task to build a deployment bundle for a trained run.

    Validates ownership and training status eagerly so the caller receives an
    immediate HTTP error rather than a silently failed task.

    Args:
        run_id (int): Primary key of the run to deploy.
        request (DeployRequest): Bundle name provided by the user.
        db (Session): SQLAlchemy session.
        user (UserInfo): Authenticated user resolved by get_current_user.

    Raises:
        EntityNotFoundError: Run not found or not owned by this user (→ 404).
        InvalidStateError: Training has not completed successfully (→ 409).

    Returns:
        dict: Celery task ID for polling via the activity monitor.
    """
    run = run_repository.get_by_id(db, run_id, owner_id=user.sub)
    if run is None:
        raise EntityNotFoundError("Run", run_id)
    if run.training_status != TrainingStatus.success:
        raise InvalidStateError("Cannot deploy a run that has not completed training successfully.")
    if run.deploy_task_id is not None or run.deploy_artifact_key is not None:
        raise InvalidStateError("A deployment is already in progress or completed for this run.")

    task = run_deployment.delay(run_id, user.sub, request.name)
    update_deploy_task_id(db, run_id=run_id, deploy_task_id=task.id)
    return {"task_id": task.id}


@router.get("/{run_id}/deploy/download", status_code=status.HTTP_200_OK)
def download_bundle(
    run_id: int,
    db: Session = Depends(get_db),
    user: UserInfo = Depends(get_current_user),
):
    """Generate a fresh presigned URL for an existing bundle and return it.

    The presigned URL is valid for 5 minutes. Re-clicking the button always
    generates a new URL so there is no stale-link problem.

    Args:
        run_id (int): Primary key of the run.
        db (Session): SQLAlchemy session.
        user (UserInfo): Authenticated user resolved by get_current_user.

    Raises:
        EntityNotFoundError: Run not found or not owned by this user (→ 404).
        InvalidStateError: No bundle has been built for this run yet (→ 409).

    Returns:
        dict: Presigned URL for downloading the bundle.
    """
    url = generate_download_url(db=db, run_id=run_id, user_id=user.sub)
    return {"url": url}
