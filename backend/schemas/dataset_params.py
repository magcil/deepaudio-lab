from datetime import datetime

from pydantic import BaseModel


class DatasetUploadRequest(BaseModel):
    user_id: str
    dataset_name: str
    description: str | None = None
    paths: list[str]
    total_bytes: int


class PresignedUrlItem(BaseModel):
    path: str
    key: str
    url: str


class DatasetUploadResponse(BaseModel):
    dataset_id: int
    urls: list[PresignedUrlItem]


class ConfirmUploadRequest(BaseModel):
    size_bytes: int
    num_files: int


class DatasetResponse(BaseModel):
    id: int
    name: str
    description: str | None
    s3_prefix: str
    size_bytes: int
    num_files: int
    status: str
    created_at: datetime
