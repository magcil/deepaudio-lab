from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Pydantic schema for the authentication response.

    Attributes:
        access_token (str): JWT access token issued by Keycloak.
        token_type (str): Token type, always `bearer`.
    """

    access_token: str
    token_type: str = "bearer"
