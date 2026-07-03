from jwt import PyJWKClient
from pydantic_settings import BaseSettings, SettingsConfigDict


class KeycloakSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    keycloak_server_url: str
    keycloak_realm: str


settings = KeycloakSettings()  # type: ignore[call-arg]

# The backend is a pure token *verifier*. It reads the realm's public signing keys
# from the JWKS (JSON Web Key Set) endpoint and validates JWT signatures locally —
# no client, secret, or service account is involved (JWKS is a realm-level,
# unauthenticated endpoint). PyJWKClient caches the key set (5 min by default) and
# selects the right key by the token's `kid` header, so verification keeps working
# across Keycloak signing-key rotation.
_JWKS_URL = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"

jwks_client = PyJWKClient(_JWKS_URL)
