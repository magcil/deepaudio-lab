import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from exceptions.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    ReferencedEntityNotFoundError,
    ResourceNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    # Handle RequestValidationError
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