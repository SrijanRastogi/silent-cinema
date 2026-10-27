"""Stable error envelope and exception handlers.

Every error response has the shape documented in ``API.md`` §2. Internal
details are logged, never returned.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("silent_cinema.errors")


class ErrorDetail(BaseModel):
    """One field-level reason inside an error response."""

    field: str | None = None
    reason: str


class ErrorBody(BaseModel):
    """Stable machine-readable error information."""

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: str


class ErrorEnvelope(BaseModel):
    """Top-level error response wrapper."""

    error: ErrorBody


class AppError(Exception):
    """A domain error that maps to a documented code and HTTP status."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


_STATUS_CODES = {
    400: "bad_request",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "upload_too_large",
    415: "unsupported_media",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    503: "service_unavailable",
}


def request_id(request: Request) -> str:
    """Read the request id established by the request-id middleware."""
    value = getattr(request.state, "request_id", None)
    return value if isinstance(value, str) else "unknown"


def _response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or [],
            request_id=request_id(request),
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle explicit domain errors."""
    if not isinstance(exc, AppError):
        return await internal_error_handler(request, exc)
    return _response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle routing and framework HTTP errors without leaking internals."""
    if not isinstance(exc, StarletteHTTPException):
        return await internal_error_handler(request, exc)

    code = _STATUS_CODES.get(exc.status_code, "http_error")
    messages = {
        404: "Resource not found.",
        405: "Method not allowed for this resource.",
    }
    detail = messages.get(exc.status_code)
    if detail is None:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return _response(request, status_code=exc.status_code, code=code, message=detail)


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert request validation failures into the error envelope."""
    if not isinstance(exc, RequestValidationError):
        return await internal_error_handler(request, exc)

    raw_errors = exc.errors()
    malformed_json = any(error.get("type") == "json_invalid" for error in raw_errors)
    details = []
    for error in raw_errors:
        location = [
            str(part) for part in error.get("loc", ()) if part not in {"body", "query", "path"}
        ]
        details.append(
            ErrorDetail(
                field=".".join(location) or None,
                reason=str(error.get("msg", "Invalid value.")),
            )
        )

    if malformed_json:
        return _response(
            request,
            status_code=400,
            code="bad_request",
            message="Malformed JSON request body.",
            details=details,
        )
    return _response(
        request,
        status_code=422,
        code="validation_error",
        message="Request validation failed.",
        details=details,
    )


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log the cause and return a safe generic message."""
    logger.exception("Unhandled error request_id=%s", request_id(request), exc_info=exc)
    return _response(
        request,
        status_code=500,
        code="internal_error",
        message="An internal error occurred.",
    )


def install_error_handlers(app: Any) -> None:
    """Register handlers on a FastAPI application."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)
