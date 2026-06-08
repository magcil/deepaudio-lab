class AppError(Exception):
    """Base class for all application exceptions."""

    pass


class RepositoryError(AppError):
    """Generic repository / database error."""

    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""

    def __init__(self, entity: str, identifier: object | None = None):
        """Build a not-found error for a missing database entity.

        Args:
            entity (str): Human-readable name of the entity type (e.g. ``"Run"``).
            identifier (object | None, optional): Identifier used in the lookup
                (primary key, name, etc.). When provided it is included in the
                error message. Defaults to None.
        """
        self.entity = entity
        self.identifier = identifier
        if identifier is not None:
            super().__init__(f"{entity} '{identifier}' not found")
        else:
            super().__init__(f"{entity} not found")


class ReferencedEntityNotFoundError(AppError):
    """A referenced entity in the request body does not exist. Maps to 422."""

    def __init__(self, entity: str, identifier: object | None = None):
        """Build an error for a request referencing a non-existent entity.

        Used when a request payload points at a related row (typically via
        a foreign key) that cannot be resolved.

        Args:
            entity (str): Human-readable name of the referenced entity type.
            identifier (object | None, optional): Identifier that failed to
                resolve. Defaults to None.
        """
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"Referenced {entity} '{identifier}' does not exist")


class DuplicateEntityError(RepositoryError):
    """Raised when a uniqueness constraint is violated."""

    def __init__(self, entity: str, identifier: object | None = None):
        """Build an error for a uniqueness-constraint violation.

        Args:
            entity (str): Human-readable name of the entity type.
            identifier (object | None, optional): Identifier of the conflicting
                row (e.g. the unique name or key). When provided it is included
                in the error message. Defaults to None.
        """
        self.entity = entity
        self.identifier = identifier
        if identifier is not None:
            super().__init__(f"{entity} '{identifier}' already exists")
        else:
            super().__init__(f"{entity} already exists")


class ResourceNotFoundError(AppError):
    """A non-database resource (file, external service, etc.) was not found."""

    def __init__(self, resource_type: str, identifier: object | None = None):
        """Build an error for a missing external resource.

        Args:
            resource_type (str): Category of the resource (e.g. ``"dataset"``,
                ``"checkpoint"``, ``"config file"``).
            identifier (object | None, optional): Locator for the resource,
                such as a filesystem path or URL. Defaults to None.
        """
        self.resource_type = resource_type
        self.identifier = identifier
        if identifier is not None:
            super().__init__(f"{resource_type} '{identifier}' not found")
        else:
            super().__init__(f"{resource_type} not found")


class InvalidResourceError(AppError):
    """A resource exists but is malformed or unreadable."""

    def __init__(self, resource_type: str, identifier: object | None = None, reason: str | None = None):
        """Build an error for a resource that exists but cannot be used.

        Args:
            resource_type (str): Category of the resource (e.g. ``"config file"``,
                ``"checkpoint"``).
            identifier (object | None, optional): Locator for the resource,
                such as a filesystem path or URL. Defaults to None.
            reason (str | None, optional): Short explanation of why the
                resource is invalid (parse failure, schema mismatch, …).
                Appended to the error message when given. Defaults to None.
        """
        self.resource_type = resource_type
        self.identifier = identifier
        self.reason = reason
        msg = f"{resource_type} '{identifier}' is invalid"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class UnauthorizedError(AppError):
    """Raised when a user attempts to access a resource they do not own."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message)


class InvalidStateError(AppError):
    """Raised when an operation violates domain state constraints.

    This exception is used when a request is syntactically valid but
    cannot be executed because the current system state makes the
    operation invalid (e.g. attempting to evaluate an already evaluated run).

    Attributes:
        message (str): Human-readable explanation of the state violation.
    """

    def __init__(self, message: str):
        """Initialize an InvalidStateError.

        Args:
            message (str): Detailed explanation of why the current state
                prevents the requested operation.
        """
        super().__init__(message)


class QuotaExceededError(AppError):
    """Raised when a user's storage quota would be exceeded by an upload.

    Maps to HTTP 413 Request Entity Too Large.

    Attributes:
        used (int): Bytes already consumed by the user.
        limit (int): Maximum bytes allowed for the user.
        requested (int): Bytes the user is attempting to upload.
    """

    def __init__(self, used: int, limit: int, requested: int):
        """Initialize a QuotaExceededError.

        Args:
            used (int): Bytes already consumed by the user.
            limit (int): Maximum bytes allowed for the user.
            requested (int): Bytes the user is attempting to upload.
        """
        self.used = used
        self.limit = limit
        self.requested = requested
        remaining = limit - used
        super().__init__(
            f"Upload of {requested:,} bytes would exceed quota. "
            f"Used: {used:,} / {limit:,} bytes. "
            f"Remaining: {remaining:,} bytes."
        )

class UnprocessableEntityError(AppError):
    """Raised when a request is well-formed but semantically invalid.

    Maps to HTTP 422 Unprocessable Entity.
    """

    def __init__(self, message: str):
        """Initialize an UnprocessableEntityError.

        Args:
            message (str): Detailed explanation of why the request cannot be processed.
        """
        super().__init__(message)

        
class InsufficientStorageError(AppError):
    """Raised when the server lacks storage needed to complete the request.

    Maps to HTTP 507 Insufficient Storage.

    Attributes:
        used (int): Bytes already consumed by the whole system.
        limit (int): Maximum bytes allowed for the whole system.
        requested (int): Bytes the user is attempting to upload.
    """

    def __init__(self, used: int, limit: int, requested: int):
        """Initialize an InsufficientStorageError.

        Args:
            used (int): Bytes already consumed by the whole system.
            limit (int): Maximum bytes allowed for whole system.
            requested (int): Bytes the user is attempting to upload.
        """
        self.used = used
        self.limit = limit
        self.requested = requested
        remaining = limit - used
        super().__init__(
            f"Upload of {requested:,} bytes would exceed total storage. "
            f"Used: {used:,} / {limit:,} bytes. "
            f"System has remaining: {remaining:,} bytes."
        )