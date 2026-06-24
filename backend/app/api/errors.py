from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiException(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)


async def api_exception_handler(_: Request, exc: ApiException) -> JSONResponse:
    return error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def request_validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    normalized_errors = [
        {
            "field": _normalize_location(error.get("loc", ())),
            "message": error.get("msg", "Invalid value"),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    first_error = normalized_errors[0] if normalized_errors else None
    if first_error and first_error["field"]:
        message = (
            f"Validation failed for {first_error['field']}: "
            f"{first_error['message']}"
        )
    elif first_error:
        message = f"Validation failed: {first_error['message']}"
    else:
        message = "Validation failed"

    return error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message=message,
        details={"errors": normalized_errors},
    )


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> JSONResponse:
    payload = {
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def _normalize_location(location: tuple[Any, ...]) -> str:
    parts = [str(part) for part in location if part != "body"]
    return ".".join(parts)
