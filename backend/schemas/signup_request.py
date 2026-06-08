from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    """Pydantic schema for new user registration payload.

    Attributes:
        username (str): Desired Keycloak username.
        email (EmailStr): User's email address (validated format).
        password (str): Desired account password.
        first_name (str): User's first name.
        last_name (str): User's last name.
    """

    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
