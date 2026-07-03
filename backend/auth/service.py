import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClientError
from sqlalchemy.orm import Session

from auth.keycloak import jwks_client
from db.session import get_db
from repositories import user_repository
from schemas.user_info import UserInfo

bearer_scheme = HTTPBearer()


def verify_token(token: str) -> UserInfo:
    """Verify a Keycloak JWT and extract the user's identity and roles.

    Resolves the realm's RS256 signing key from the JWKS endpoint (by the token's
    `kid`) and validates the signature locally. Extracts standard OIDC claims
    (`sub`, `preferred_username`, `email`, `given_name`, `family_name`) and realm
    roles from the `realm_access` claim.

    Args:
        token (str): A raw JWT access token issued by Keycloak.

    Raises:
        HTTPException 401: If the token has expired.
        HTTPException 401: If the token is invalid, cannot be decoded, or its
            signing key cannot be resolved from the realm's JWKS.

    Returns:
        UserInfo: The authenticated user's identity and assigned realm roles.
    """
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
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
    except (jwt.InvalidTokenError, PyJWKClientError):
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
            status_code=status.HTTP_403_FORBIDDEN, detail="Only regular users can perform this action"
        ) from None
    return user
