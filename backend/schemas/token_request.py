from pydantic import BaseModel


class TokenRequest(BaseModel):
    username: str
    password: str