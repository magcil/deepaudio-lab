import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError
from sqlalchemy.orm import Session

from db.session import get_db
from auth.keycloak import keycloak_admin, keycloak_openid
from repositories import user_repository
from schemas.signup_request import SignupRequest
from schemas.user_info import UserInfo

bearer_scheme = HTTPBearer()


def register_user(db: Session, data: SignupRequest) -> dict:
    """Create a new user in Keycloak and sync their profile to the local database.

    Registers the user in the Keycloak `deepaudiolab` realm, assigns the `regular`
    realm role, and upserts a corresponding record in the local `user` table.

    Args:
        db (Session): SQLAlchemy database session.
        data (SignupRequest): Registration payload containing username, email,
            first name, last name, and password.

    Raises:
        HTTPException 409: If the username or email already exists in Keycloak.
        HTTPException 500: If user creation fails for any other reason.

    Returns:
        dict: A dictionary with the newly created user's `id` and `username`.
    """
    try:
        user_id = keycloak_admin.create_user(
            {
                "username": data.username,
                "email": data.email,
                "firstName": data.first_name,
                "lastName": data.last_name,
                "enabled": True,
                "credentials": [
                    {
                        "type": "password",
                        "value": data.password,
                        "temporary": False
                    }
                ],
            },
            exist_ok=False,
        )

        keycloak_admin.assign_realm_roles(
            user_id,
            [keycloak_admin.get_realm_role("regular")]
        )

        user_repository.upsert(
            db,
            id=user_id,
            username=data.username,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
        )

        return {"id": user_id, "username": data.username}
    except KeycloakPostError as e:
        if e.response_code == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists",
            ) from None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user",
        ) from None


def delete_user(db: Session, username: str) -> None:
    """Delete a user from Keycloak and the local database.

    Looks up the user by username in Keycloak, removes them from the
    `deepaudiolab` realm, and deletes the corresponding local `user` record.

    Args:
        db (Session): SQLAlchemy database session.
        username (str): The Keycloak username of the user to delete.

    Raises:
        HTTPException 404: If no user with the given username exists in Keycloak.
    """
    user_id = keycloak_admin.get_user_id(username)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        ) from None
    keycloak_admin.delete_user(user_id)
    user_repository.delete_by_id(db, user_id)


def authenticate_user(username: str, password: str) -> str:
    """Authenticate a user against Keycloak and return a JWT access token.

    Uses the OAuth2 Resource Owner Password Credentials (Direct Access Grant)
    flow to exchange the provided credentials for a token issued by Keycloak.

    Args:
        username (str): The user's Keycloak username.
        password (str): The user's password.

    Raises:
        HTTPException 401: If the username or password is incorrect.

    Returns:
        str: A signed JWT access token issued by Keycloak.
    """
    try:
        token = keycloak_openid.token(username, password)
        return token["access_token"]
    except (KeycloakAuthenticationError, KeycloakPostError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        ) from None


def _get_public_key() -> str:
    """Fetch the Keycloak realm's RS256 public key in PEM format.

    Retrieves the raw public key from Keycloak's OpenID Connect endpoint
    and wraps it with PEM headers so it can be used directly by PyJWT
    for JWT signature verification.

    Returns:
        str: The realm's public key as a PEM-encoded string.
    """
    return (
        "-----BEGIN PUBLIC KEY-----\n"
        + keycloak_openid.public_key()
        + "\n-----END PUBLIC KEY-----"
    )


def verify_token(token: str) -> UserInfo:
    """Verify a Keycloak JWT and extract the user's identity and roles.

    Decodes and validates the token signature using the realm's RS256 public key.
    Extracts standard OIDC claims (`sub`, `preferred_username`, `email`,
    `given_name`, `family_name`) and realm roles from the `realm_access` claim.

    Args:
        token (str): A raw JWT access token issued by Keycloak.

    Raises:
        HTTPException 401: If the token has expired.
        HTTPException 401: If the token is invalid or cannot be decoded.

    Returns:
        UserInfo: The authenticated user's identity and assigned realm roles.
    """
    try:
        claims = jwt.decode(
            token,
            _get_public_key(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        roles = claims.get("realm_access", {}).get("roles", [])
        return UserInfo(
            sub=claims["sub"],
            username=claims["preferred_username"],
            email=claims.get("email"),
            first_name=claims.get("given_name"),
            last_name=claims.get("family_name"),
            roles=roles,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserInfo:
    """FastAPI dependency that resolves the authenticated user from a Bearer token.

    Verifies the JWT from the `Authorization` header, upserts the user's profile
    in the local database (so the local `user` table stays in sync with Keycloak),
    and returns the resolved identity.

    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token extracted from
            the `Authorization` header by FastAPI's `HTTPBearer` scheme.
        db (Session): SQLAlchemy database session.

    Returns:
        UserInfo: The authenticated user's identity and realm roles.
    """
    user = verify_token(credentials.credentials)
    user_repository.upsert(
        db,
        id=user.sub,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    return user


def require_admin(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """FastAPI dependency that restricts access to users with the `admin` realm role.

    Args:
        user (UserInfo): The authenticated user resolved by `get_current_user`.

    Raises:
        HTTPException 403: If the authenticated user does not have the `admin` role.

    Returns:
        UserInfo: The authenticated admin user.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        ) from None
    return user


def require_regular(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """FastAPI dependency that restricts access to users with the `regular` realm role.

    Args:
        user (UserInfo): The authenticated user resolved by `get_current_user`.

    Raises:
        HTTPException 403: If the authenticated user does not have the `regular` role.

    Returns:
        UserInfo: The authenticated regular user.
    """
    if not user.is_regular:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only regular users can perform this action"
        ) from None
    return user
