from pydantic import BaseModel, computed_field


class UserInfo(BaseModel):
    """Pydantic model representing the authenticated user's identity and realm roles.

    Populated from Keycloak JWT claims after token verification.

    Attributes:
        sub (str): Keycloak subject identifier (unique user ID).
        username (str): The user's Keycloak username.
        email (str | None): The user's email address.
        first_name (str | None): The user's first name.
        last_name (str | None): The user's last name.
        roles (list[str]): Realm roles assigned to the user in Keycloak.
        is_admin (bool): True if the user has the `admin` realm role.
        is_regular (bool): True if the user has the `regular` realm role.
    """

    sub: str
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    roles: list[str] = []

    @computed_field
    @property
    def is_admin(self) -> bool:
        """Check whether the user holds the `admin` realm role.

        Returns:
            bool: True if `admin` is present in the user's roles.
        """
        return "admin" in self.roles

    @computed_field
    @property
    def is_regular(self) -> bool:
        """Check whether the user holds the `regular` realm role.

        Returns:
            bool: True if `regular` is present in the user's roles.
        """
        return "regular" in self.roles
