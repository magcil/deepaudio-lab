import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from exceptions.exceptions import EntityNotFoundError, QuotaExceededError, InsufficientStorageError
from models.dataset import Dataset, DatasetStatus
from repositories import dataset_repository
from services import storage_service
from services.storage_service import put_user_presigned_url
from storage.client import DATA_BUCKET, s3_client
from config.limits import USER_SPACE_LIMIT, TOTAL_STORAGE_LIMIT
load_dotenv()


def get_total_storage_used(bucket: str) -> int:
    paginator = s3_client.get_paginator("list_objects_v2")
    total = 0
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            total += obj["Size"]
    return total

def request_upload(
    db: Session,
    user_id: str,
    dataset_name: str,
    description: str | None,
    paths: list[str],
    total_bytes: int,
) -> dict:
    """Validate quota, register a new dataset, and return presigned upload URLs.

    Checks whether the user and the system has enough remaining storage 
    capacity before creating the Dataset row in ``uploading`` status and 
    generating one presigned PUT URL per file path.

    Args:
        db (Session): Active SQLAlchemy session.
        user_id (str): Owner of the dataset.
        dataset_name (str): Human-readable name for the new dataset.
            Must be unique per user.
        description (str | None): Optional free-text description.
        paths (list[str]): Relative file paths to upload
            (e.g. ``["gtzan/train/blues/track01.wav"]``).
        total_bytes (int): Total size of all files, as reported by the
            browser's ``File.size`` sum.

    Raises:
        QuotaExceededError: If ``current_usage + total_bytes`` exceeds
            ``USER_SPACE_LIMIT``.
        QuotaExceededError: If ``current_usage + total_bytes`` exceeds
            ``TOTAL_SPACE_LIMIT``.
        DuplicateEntityError: If the user already has a dataset with
            the same name.

    Returns:
        dict: ``{"dataset_id": int, "urls": [{"path", "key", "url"}, ...]}``
    """
    total_used_by_system = get_total_storage_used(DATA_BUCKET)
    used = dataset_repository.get_total_size_by_user(db, user_id)
    
    if total_used_by_system + total_bytes > TOTAL_STORAGE_LIMIT:
        raise InsufficientStorageError(
            used=total_used_by_system, 
            limit=TOTAL_STORAGE_LIMIT, 
            requested=total_bytes
        )
    if used + total_bytes > USER_SPACE_LIMIT:
        raise QuotaExceededError(
            used=used,
            limit=USER_SPACE_LIMIT, 
            requested=total_bytes
        )

    dataset = Dataset(
        user_id=user_id,
        name=dataset_name,
        description=description,
        s3_prefix="",
        size_bytes=0,
        num_files=len(paths),
    )
    created = dataset_repository.create(db, dataset)
    created = dataset_repository.set_s3_prefix(db, created, f"{user_id}/{created.id}/")

    urls = []
    for path in paths:
        path_without_root = "/".join(path.split("/")[1:])
        key, url = put_user_presigned_url(
            user=user_id, bucket=DATA_BUCKET, suffix_file_path=f"{created.id}/{path_without_root}"
        )
        urls.append({"path": path, "key": key, "url": url})

    return {"dataset_id": created.id, "urls": urls}


def confirm_upload(db: Session, dataset_id: int, size_bytes: int, num_files: int) -> dict:
    """Mark a dataset upload as complete and record its final size and file count.

    Called by the frontend after all presigned uploads have succeeded.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset_id (int): ID of the dataset to confirm.
        size_bytes (int): Actual total bytes uploaded.
        num_files (int): Actual number of files uploaded.

    Raises:
        EntityNotFoundError: If no dataset with the given ID exists.

    Returns:
        dict: Serialized Dataset with status set to ``ready``.
    """
    dataset = dataset_repository.confirm(db, dataset_id, size_bytes, num_files)
    return _serialize(dataset)


def report_error(db: Session, dataset_id: int) -> dict:
    """Mark a dataset upload as failed.

    Called by the frontend when one or more presigned uploads fail and
    the upload cannot be recovered.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset_id (int): ID of the dataset to mark as failed.

    Raises:
        EntityNotFoundError: If no dataset with the given ID exists.

    Returns:
        dict: Serialized Dataset with status set to ``error``.
    """
    dataset = dataset_repository.update_status(db, dataset_id, DatasetStatus.error)
    return _serialize(dataset)


def delete(db: Session, dataset_id: int) -> None:
    """Delete a dataset and all its files from storage.

    Storage is cleared before the DB row is removed so that a storage
    failure leaves the record intact and the dataset remains trackable.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset_id (int): Primary key of the Dataset to delete.

    Raises:
        EntityNotFoundError: If no dataset with the given ID exists.
    """
    dataset = dataset_repository.get_by_id(db, dataset_id)
    if dataset is None:
        raise EntityNotFoundError("Dataset", dataset_id)
    storage_service.delete_dataset_files(str(dataset.s3_prefix))
    dataset_repository.delete(db, dataset_id)


def get_splits(db: Session, dataset_id: int) -> list[str]:
    """List the top-level split directories stored under a dataset's S3 prefix.

    Uses the S3 delimiter API to discover virtual subdirectories without
    downloading any file content (e.g. ``["train", "val"]``).

    Args:
        db (Session): Active SQLAlchemy session.
        dataset_id (int): Primary key of the Dataset to inspect.

    Raises:
        EntityNotFoundError: If no dataset with the given ID exists.

    Returns:
        list[str]: Sorted list of split names found directly under the prefix.
    """
    dataset = dataset_repository.get_by_id(db, dataset_id)
    if dataset is None:
        raise EntityNotFoundError("Dataset", dataset_id)

    prefix = str(dataset.s3_prefix)
    paginator = s3_client.get_paginator("list_objects_v2")
    splits: list[str] = []
    for page in paginator.paginate(Bucket=DATA_BUCKET, Prefix=prefix, Delimiter="/"):
        for cp in page.get("CommonPrefixes", []):
            split = cp["Prefix"].rstrip("/").split("/")[-1]
            splits.append(split)

    return sorted(splits)


def get_all_for_user(db: Session, user_id: str) -> list[dict]:
    """Retrieve all datasets owned by a user.

    Args:
        db (Session): Active SQLAlchemy session.
        user_id (str): Owner identifier to filter by.

    Returns:
        list[dict]: Serialized list of Dataset records.
    """
    datasets = dataset_repository.get_by_user(db, user_id)
    return [_serialize(d) for d in datasets]


def _serialize(dataset: Dataset) -> dict:
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "s3_prefix": dataset.s3_prefix,
        "size_bytes": dataset.size_bytes,
        "num_files": dataset.num_files,
        "status": dataset.status,
        "created_at": dataset.created_at,
    }
