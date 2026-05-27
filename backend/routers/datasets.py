from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.dataset_params import (
    ConfirmUploadRequest,
    DatasetResponse,
    DatasetUploadRequest,
    DatasetUploadResponse,
)
from services import dataset_service

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post(
    "/presigned",
    status_code=status.HTTP_201_CREATED,
    response_model=DatasetUploadResponse,
)
def request_upload(request: DatasetUploadRequest, db: Session = Depends(get_db)):
    """Check quota, register a new dataset, and return presigned upload URLs.

    Args:
        request (DatasetUploadRequest): Upload request containing the user ID,
            dataset name, optional description, file paths, and total byte count.
        db (Session): SQLAlchemy session injected by FastAPI.

    Raises:
        QuotaExceededError: If the upload would exceed the user's storage limit (→ 413).
        DuplicateEntityError: If the user already has a dataset with the same name (→ 409).

    Returns:
        DatasetUploadResponse: The new dataset ID and a presigned URL for each file.
    """
    return dataset_service.request_upload(
        db=db,
        user_id=request.user_id,
        dataset_name=request.dataset_name,
        description=request.description,
        paths=request.paths,
        total_bytes=request.total_bytes,
    )


@router.post(
    "/{dataset_id}/confirm",
    status_code=status.HTTP_200_OK,
    response_model=DatasetResponse,
)
def confirm_upload(
    dataset_id: int,
    request: ConfirmUploadRequest,
    db: Session = Depends(get_db),
):
    """Mark a dataset upload as complete and record the final size and file count.

    Called by the frontend after all presigned PUT requests succeed.

    Args:
        dataset_id (int): ID of the dataset to confirm.
        request (ConfirmUploadRequest): Actual size in bytes and number of files uploaded.
        db (Session): SQLAlchemy session injected by FastAPI.

    Raises:
        EntityNotFoundError: If no dataset with the given ID exists (→ 404).

    Returns:
        DatasetResponse: Updated dataset record with status set to ``ready``.
    """
    return dataset_service.confirm_upload(
        db=db,
        dataset_id=dataset_id,
        size_bytes=request.size_bytes,
        num_files=request.num_files,
    )


@router.patch(
    "/{dataset_id}/error",
    status_code=status.HTTP_200_OK,
    response_model=DatasetResponse,
)
def report_error(dataset_id: int, db: Session = Depends(get_db)):
    """Mark a dataset upload as failed.

    Called by the frontend when one or more presigned uploads fail and
    the upload cannot be recovered.

    Args:
        dataset_id (int): ID of the dataset to mark as failed.
        db (Session): SQLAlchemy session injected by FastAPI.

    Raises:
        EntityNotFoundError: If no dataset with the given ID exists (→ 404).

    Returns:
        DatasetResponse: Updated dataset record with status set to ``error``.
    """
    return dataset_service.report_error(db=db, dataset_id=dataset_id)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[DatasetResponse],
)
def get_datasets(user_id: str, db: Session = Depends(get_db)):
    """Retrieve all datasets owned by a user.

    Args:
        user_id (str): Query parameter identifying the owner.
        db (Session): SQLAlchemy session injected by FastAPI.

    Returns:
        list[DatasetResponse]: All dataset records for the given user.
    """
    return dataset_service.get_all_for_user(db=db, user_id=user_id)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Delete a dataset and all its files from storage.

    Args:
        dataset_id (int): ID of the dataset to delete.
        db (Session): SQLAlchemy session injected by FastAPI.

    Raises:
        EntityNotFoundError: If no dataset with the given ID exists (→ 404).
    """
    dataset_service.delete(db=db, dataset_id=dataset_id)
