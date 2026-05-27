from pydantic import Field
from pydantic_settings import BaseSettings

from keycloak import KeycloakAdmin, KeycloakOpenID, KeycloakOpenIDConnection


class KeycloakSettings(BaseSettings):
    """Loads Keycloak connection settings from environment variables or a `.env` file."""

    keycloak_server_url: str = Field(..., env="KEYCLOAK_SERVER_URL")
    keycloak_realm: str = Field(..., env="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(..., env="KEYCLOAK_CLIENT_ID")
    keycloak_client_secret: str = Field(..., env="KEYCLOAK_CLIENT_SECRET")

    class Config:
        """Instructs Pydantic to read values from `backend/.env`, using UTF-8 encoding.
        Any extra variables present in the file but not defined in this model are silently ignored.
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
settings = KeycloakSettings()

keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_server_url,
    realm_name=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
    client_secret_key=settings.keycloak_client_secret,
)

_connection = KeycloakOpenIDConnection(
    server_url=settings.keycloak_server_url,
    realm_name=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
    client_secret_key=settings.keycloak_client_secret,
    verify=True,
)

keycloak_admin = KeycloakAdmin(connection=_connection)