from pydantic import BaseModel


class PresignRequest(BaseModel):
    paths: list[str]
    user: str


class PresignedItem(BaseModel):
    path: str
    key: str
    url: str


class PresignResponse(BaseModel):
    urls: list[PresignedItem]
