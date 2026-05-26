from pydantic import BaseModel, computed_field
from typing import Optional


class UserInfo(BaseModel):
    sub: str
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: list[str] = []

    @computed_field
    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    @computed_field
    @property
    def is_regular(self) -> bool:
        return "regular" in self.roles
