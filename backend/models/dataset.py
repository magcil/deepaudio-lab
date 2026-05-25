import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from db.session import Base


class DatasetStatus(str, enum.Enum):
    """Lifecycle state of a user dataset.

    Attributes:
        uploading: Presigned URLs have been issued; upload is in progress.
        ready: Upload confirmed complete; dataset is usable for training/evaluation.
        error: Upload failed or was only partially completed.
    """

    uploading = "uploading"
    ready = "ready"
    error = "error"


class Dataset(Base):
    """Represents a user-owned dataset stored in SeaweedFS.

    Tracks metadata and upload status for datasets uploaded by users.
    In the current single-user iteration ``user_id`` is the plain string
    ``"default"``.  Once Keycloak is integrated it will hold the Keycloak
    ``sub`` UUID and a FK constraint to the ``user`` table will be added via
    migration.

    A uniqueness constraint on ``(user_id, name)`` prevents the same user
    from registering two datasets with the same name (which would collide
    on the same S3 prefix).

    Attributes:
        id (int): Primary key.
        user_id (str): Owner identifier. Plain string for now; FK added when
            Keycloak user management lands.
        name (str): Human-readable dataset name, unique per user.
        description (str | None): Optional free-text description.
        s3_prefix (str): Base S3 key prefix, e.g. ``"default/gtzan/"``.
        size_bytes (int): Total size of all uploaded files in bytes.
            Starts at 0 and is updated when the upload is confirmed complete.
        num_files (int): Total number of audio files in the dataset.
            Updated together with ``size_bytes`` on upload confirmation.
        status (DatasetStatus): Current lifecycle state of the dataset.
        created_at (datetime): Timestamp when the dataset record was created.
    """

    __tablename__ = "dataset"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    s3_prefix = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    num_files = Column(Integer, nullable=False, default=0)
    status = Column(
        Enum(DatasetStatus, native_enum=False),
        nullable=False,
        default=DatasetStatus.uploading,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_dataset_user_name"),)
