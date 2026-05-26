import jwt

from config import keycloak_admin, keycloak_openid
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from db.session import get_db
from repositories import user_repository
from schemas.signup_request import SignupRequest
from schemas.user_info import UserInfo

bearer_scheme = HTTPBearer()


def register_user(db: Session, data: SignupRequest) -> dict:
    try:
        user_id = keycloak_admin.create_user(
            {
                "username": data.username,
                "email": data.email,
                "firstName": data.first_name,
                "lastName": data.last_name,
                "enabled": True,
                "credentials": [
                    {"type": "password", "value": data.password, "temporary": False}
                ],
            },
            exist_ok=False,
        )
        regular_role = keycloak_admin.get_realm_role("regular")
        keycloak_admin.assign_realm_roles(user_id, [regular_role])
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
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user",
        )


def delete_user(db: Session, username: str) -> None:
    user_id = keycloak_admin.get_user_id(username)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{username}' not found")
    keycloak_admin.delete_user(user_id)
    user_repository.delete_by_id(db, user_id)


def authenticate_user(username: str, password: str) -> str:
    try:
        token = keycloak_openid.token(username, password)
        return token["access_token"]
    except (KeycloakAuthenticationError, KeycloakPostError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )


def _get_public_key() -> str:
    return (
        "-----BEGIN PUBLIC KEY-----\n"
        + keycloak_openid.public_key()
        + "\n-----END PUBLIC KEY-----"
    )


def verify_token(token: str) -> UserInfo:
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
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserInfo:
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
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_regular(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    if not user.is_regular:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only regular users can perform this action")
    return user