import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from exceptions.exceptions import QuotaExceededError
from models.dataset import Dataset, DatasetStatus
from repositories import dataset_repository
from services.storage_service import put_user_presigned_url
from storage.client import DATA_BUCKET

load_dotenv()

USER_SPACE_LIMIT: int = int(os.getenv("USER_SPACE_LIMIT", 10 * 1024**3))


def request_upload(
    db: Session,
    user_id: str,
    dataset_name: str,
    description: str | None,
    paths: list[str],
    total_bytes: int,
) -> dict:
    """Validate quota, register a new dataset, and return presigned upload URLs.

    Checks whether the user has enough remaining storage capacity before
    creating the Dataset row in ``uploading`` status and generating one
    presigned PUT URL per file path.

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
        DuplicateEntityError: If the user already has a dataset with
            the same name.

    Returns:
        dict: ``{"dataset_id": int, "urls": [{"path", "key", "url"}, ...]}``
    """
    used = dataset_repository.get_total_size_by_user(db, user_id)
    if used + total_bytes > USER_SPACE_LIMIT:
        raise QuotaExceededError(used=used, limit=USER_SPACE_LIMIT, requested=total_bytes)

    dataset = Dataset(
        user_id=user_id,
        name=dataset_name,
        description=description,
        s3_prefix=f"{user_id}/{dataset_name}/",
        size_bytes=0,
        num_files=len(paths),
    )
    created = dataset_repository.create(db, dataset)

    urls = []
    for path in paths:
        key, url = put_user_presigned_url(user=user_id, bucket=DATA_BUCKET, suffix_file_path=path)
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
