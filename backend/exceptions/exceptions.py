class AppError(Exception):
    """Base class for all application exceptions."""
    pass


class RepositoryError(AppError):
    """Generic repository / database error."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""

    def __init__(self, entity: str, identifier: object | None = None):
        self.entity = entity
        self.identifier = identifier
        if identifier is not None:
            super().__init__(f"{entity} '{identifier}' not found")
        else:
            super().__init__(f"{entity} not found")

class ReferencedEntityNotFoundError(AppError):
    """A referenced entity in the request body does not exist. Maps to 422."""

    def __init__(self, entity: str, identifier: object | None = None):
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"Referenced {entity} '{identifier}' does not exist")

class DuplicateEntityError(RepositoryError):
    """Raised when a uniqueness constraint is violated."""

    def __init__(self, entity: str, identifier: object | None = None):
        self.entity = entity
        self.identifier = identifier
        if identifier is not None:
            super().__init__(f"{entity} '{identifier}' already exists")
        else:
            super().__init__(f"{entity} already exists")

class ResourceNotFoundError(AppError):
    """A non-database resource (file, external service, etc.) was not found."""

    def __init__(self, resource_type: str, identifier: object | None = None):
        self.resource_type = resource_type
        self.identifier = identifier
        if identifier is not None:
            super().__init__(f"{resource_type} '{identifier}' not found")
        else:
            super().__init__(f"{resource_type} not found")


class InvalidResourceError(AppError):
    """A resource exists but is malformed or unreadable."""

    def __init__(self, resource_type: str, identifier: object | None = None, reason: str | None = None):
        self.resource_type = resource_type
        self.identifier = identifier
        self.reason = reason
        msg = f"{resource_type} '{identifier}' is invalid"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)