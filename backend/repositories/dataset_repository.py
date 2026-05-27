from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from exceptions.exceptions import DuplicateEntityError, EntityNotFoundError, RepositoryError
from models.dataset import Dataset, DatasetStatus


def create(db: Session, dataset: Dataset) -> Dataset:
    """Persist a new Dataset record.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset (Dataset): Unsaved Dataset instance to insert.

    Raises:
        DuplicateEntityError: If a dataset with the same (user_id, name) already exists.
        RepositoryError: If any other database error occurs.

    Returns:
        Dataset: The persisted and refreshed Dataset instance.
    """
    try:
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset
    except IntegrityError as e:
        db.rollback()
        raise DuplicateEntityError("Dataset", dataset.name) from e
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError("Failed to create dataset") from e


def set_s3_prefix(db: Session, dataset: Dataset, s3_prefix: str) -> Dataset:
    """Set the s3_prefix on an already-persisted Dataset.

    Called immediately after create() once the auto-generated ID is known,
    so the prefix can be namespaced by that ID.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset (Dataset): The persisted Dataset instance to update.
        s3_prefix (str): Storage prefix to assign (e.g. ``"default/1/"``).

    Raises:
        RepositoryError: If a database error occurs.

    Returns:
        Dataset: The updated and refreshed Dataset instance.
    """
    try:
        dataset.s3_prefix = s3_prefix
        db.commit()
        db.refresh(dataset)
        return dataset
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to set s3_prefix for dataset '{dataset.id}'") from e


def get_by_id(db: Session, dataset_id: int) -> Dataset | None:
    """Retrieve a Dataset by its primary key.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset_id (int): Primary key of the Dataset.

    Raises:
        RepositoryError: If a database query error occurs.

    Returns:
        Dataset | None: Matching Dataset instance or None if not found.
    """
    try:
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to fetch dataset by ID '{dataset_id}'") from e


def get_by_user(db: Session, user_id: str) -> list[Dataset]:
    """Retrieve all Dataset records belonging to a user.

    Args:
        db (Session): Active SQLAlchemy session.
        user_id (str): Owner identifier to filter by.

    Raises:
        RepositoryError: If a database query error occurs.

    Returns:
        list[Dataset]: All Dataset instances for the given user.
    """
    try:
        return db.query(Dataset).filter(Dataset.user_id == user_id).all()
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to fetch datasets for user '{user_id}'") from e


def get_total_size_by_user(db: Session, user_id: str) -> int:
    """Return the total bytes consumed by all datasets owned by a user.

    Counts all rows regardless of status so that in-progress uploads
    are included in the quota calculation.

    Args:
        db (Session): Active SQLAlchemy session.
        user_id (str): Owner identifier to aggregate.

    Raises:
        RepositoryError: If a database query error occurs.

    Returns:
        int: Sum of size_bytes across all user datasets. Returns 0 if none exist.
    """
    try:
        result = db.query(func.coalesce(func.sum(Dataset.size_bytes), 0)).filter(Dataset.user_id == user_id).scalar()
        return int(result)
    except SQLAlchemyError as e:
        raise RepositoryError(f"Failed to compute storage usage for user '{user_id}'") from e


def confirm(db: Session, dataset_id: int, size_bytes: int, num_files: int) -> Dataset:
    """Mark a dataset upload as complete and record its final size and file count.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset_id (int): Primary key of the Dataset to confirm.
        size_bytes (int): Total bytes uploaded, as reported by the frontend.
        num_files (int): Total number of files uploaded.

    Raises:
        EntityNotFoundError: If no Dataset with the given ID exists.
        RepositoryError: If a database error occurs during the update.

    Returns:
        Dataset: The updated and refreshed Dataset instance.
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset is None:
            raise EntityNotFoundError("Dataset", dataset_id)
        dataset.size_bytes = size_bytes
        dataset.num_files = num_files
        dataset.status = DatasetStatus.ready
        db.commit()
        db.refresh(dataset)
        return dataset
    except EntityNotFoundError:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to confirm dataset '{dataset_id}'") from e


def delete(db: Session, dataset_id: int) -> bool:
    """Delete a Dataset record by its primary key.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset_id (int): Primary key of the Dataset to delete.

    Raises:
        RepositoryError: If a database error occurs during deletion.

    Returns:
        bool: ``True`` if a row was deleted, ``False`` if no dataset matched.
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset is None:
            return False
        db.delete(dataset)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to delete dataset '{dataset_id}'") from e


def update_status(db: Session, dataset_id: int, status: DatasetStatus) -> Dataset:
    """Update the status of a Dataset record.

    Args:
        db (Session): Active SQLAlchemy session.
        dataset_id (int): Primary key of the Dataset to update.
        status (DatasetStatus): New status value to apply.

    Raises:
        EntityNotFoundError: If no Dataset with the given ID exists.
        RepositoryError: If a database error occurs during the update.

    Returns:
        Dataset: The updated and refreshed Dataset instance.
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset is None:
            raise EntityNotFoundError("Dataset", dataset_id)
        dataset.status = status
        db.commit()
        db.refresh(dataset)
        return dataset
    except EntityNotFoundError:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise RepositoryError(f"Failed to update status for dataset '{dataset_id}'") from e
