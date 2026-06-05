import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from exceptions.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidResourceError,
    InvalidStateError,
    InsufficientStorageError,
    QuotaExceededError,
    ReferencedEntityNotFoundError,
    ResourceNotFoundError,
    UnauthorizedError,
    UnprocessableEntityError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        logging.warning("Validation error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(EntityNotFoundError)
    async def not_found(request: Request, exc: EntityNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ReferencedEntityNotFoundError)
    async def ref_not_found(request: Request, exc: ReferencedEntityNotFoundError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(DuplicateEntityError)
    async def duplicate(request: Request, exc: DuplicateEntityError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(InvalidResourceError)
    async def invalid_resource(request: Request, exc: InvalidResourceError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})


    @app.exception_handler(UnprocessableEntityError)
    async def unprocessable_entity(request: Request, exc: UnprocessableEntityError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized(request: Request, exc: UnauthorizedError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(QuotaExceededError)
    async def quota_exceeded(request: Request, exc: QuotaExceededError):
        return JSONResponse(status_code=413, content={"detail": str(exc)})

    @app.exception_handler(InsufficientStorageError)
    async def insufficient_storage(request: Request, exc: InsufficientStorageError):
        return JSONResponse(status_code=507, content={"detail": str(exc)})

    @app.exception_handler(InvalidStateError)
    async def invalid_state(request: Request, exc: InvalidStateError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})
