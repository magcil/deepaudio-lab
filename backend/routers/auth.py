# routers/auth.py

from fastapi import APIRouter, Depends, Form, status
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.signup_request import SignupRequest
from schemas.token_response import TokenResponse
from schemas.user_info import UserInfo
from services.auth_service import authenticate_user, delete_user, register_user, require_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)) -> dict:
    """Register a new user in Keycloak and sync their profile to the local database.

    Creates the user in the Keycloak `deepaudiolab` realm, assigns the `regular`
    realm role, and upserts a corresponding record in the local `user` table.

    Args:
        data (SignupRequest): Registration payload containing username, email,
            first name, last name, and password.
        db (Session): SQLAlchemy database session (injected by FastAPI).

    Returns:
        dict: A dictionary with the newly created user's `id` and `username`.

    Raises:
        HTTPException 409: If the username or email already exists in Keycloak.
        HTTPException 500: If user creation fails for any other reason.
    """
    return register_user(db, data)


@router.post("/login", status_code=status.HTTP_200_OK)
def login(username: str = Form(...), password: str = Form(...)):
    """Authenticate a user and return a Keycloak access token.

    Uses the OAuth2 Resource Owner Password Credentials (Direct Access Grant) flow
    to exchange the provided credentials for a JWT access token issued by Keycloak.

    Args:
        username (str): The user's Keycloak username, submitted as form data.
        password (str): The user's password, submitted as form data.

    Returns:
        TokenResponse: An object containing the JWT `access_token`.

    Raises:
        HTTPException 401: If the username or password is incorrect.
    """
    access_token = authenticate_user(username, password)
    return TokenResponse(access_token=access_token)


@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(username: str, db: Session = Depends(get_db), _: UserInfo = Depends(require_admin)):
    """Delete a user from Keycloak and the local database. Admin only.

    Removes the user from the Keycloak `deepaudiolab` realm and deletes
    the corresponding record from the local `user` table. This endpoint
    is restricted to users with the `admin` realm role.

    Args:
        username (str): The username of the user to delete.
        db (Session): SQLAlchemy database session (injected by FastAPI).
        _ (UserInfo): The authenticated admin user (injected by `require_admin`).

    Raises:
        HTTPException 403: If the caller does not have the `admin` role.
        HTTPException 404: If no user with the given username exists.
    """
    delete_user(db, username)