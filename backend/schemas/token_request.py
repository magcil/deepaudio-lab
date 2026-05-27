from pydantic import BaseModel


class TokenRequest(BaseModel):
    """Pydantic schema for username/password login credentials.

    Attributes:
        username (str): The user's Keycloak username.
        password (str): The user's password.
    """
    username: str
    password: str