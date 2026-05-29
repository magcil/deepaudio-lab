from pydantic_settings import BaseSettings, SettingsConfigDict

from keycloak import KeycloakAdmin, KeycloakOpenID, KeycloakOpenIDConnection


class KeycloakSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    keycloak_server_url: str
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: str
    
settings = KeycloakSettings()  # type: ignore[call-arg]

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