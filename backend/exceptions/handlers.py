import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from exceptions.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidResourceError,
    ReferencedEntityNotFoundError,
    ResourceNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers on the FastAPI app.

    Maps the application's domain exceptions to appropriate HTTP responses
    so routers and services can raise typed errors instead of building
    ``HTTPException`` instances manually.

    Args:
        app (FastAPI): The FastAPI application to attach handlers to.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI/Pydantic request validation errors.

        Logs the offending path together with the validation errors and
        returns a 422 response whose body mirrors FastAPI's default
        validation error shape.

        Args:
            request (Request): The incoming request that failed validation.
            exc (RequestValidationError): The validation error raised by FastAPI.

        Returns:
            JSONResponse: A 422 response with the serialized validation errors.
        """
        logging.warning("Validation error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(EntityNotFoundError)
    async def not_found(request: Request, exc: EntityNotFoundError):
        """Handle lookups for entities that do not exist in the database.

        Args:
            request (Request): The incoming request.
            exc (EntityNotFoundError): The raised not-found error.

        Returns:
            JSONResponse: A 404 response carrying the exception message.
        """
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ReferencedEntityNotFoundError)
    async def ref_not_found(request: Request, exc: ReferencedEntityNotFoundError):
        """Handle requests that reference a related entity that does not exist.

        Treated as a semantic (422) error rather than 404 because the
        request itself is syntactically valid but points at a missing
        foreign-key target.

        Args:
            request (Request): The incoming request.
            exc (ReferencedEntityNotFoundError): The raised referenced-entity error.

        Returns:
            JSONResponse: A 422 response carrying the exception message.
        """
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(DuplicateEntityError)
    async def duplicate(request: Request, exc: DuplicateEntityError):
        """Handle uniqueness-constraint violations from the repository layer.

        Args:
            request (Request): The incoming request.
            exc (DuplicateEntityError): The raised duplicate-entity error.

        Returns:
            JSONResponse: A 409 response carrying the exception message.
        """
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found(request: Request, exc: ResourceNotFoundError):
        """Handle missing non-database resources (files, external services, …).

        Reported as 422 because the request is well-formed but references
        an external resource that the server cannot locate.

        Args:
            request (Request): The incoming request.
            exc (ResourceNotFoundError): The raised resource-not-found error.

        Returns:
            JSONResponse: A 422 response carrying the exception message.
        """
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(InvalidResourceError)
    async def invalid_resource(request: Request, exc: InvalidResourceError):
        """Handle malformed or unusable external resources."""
        return JSONResponse(status_code=422, content={"detail": str(exc)})
