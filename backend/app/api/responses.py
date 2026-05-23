import os
import re
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.schemas.api_response import ApiError, ApiResponse

TRACE_ID_HEADER = "X-Trace-Id"

_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_SENSITIVE_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "password",
    "secret",
    "token",
)
_SENSITIVE_ENV_NAME_PATTERN = re.compile(
    r"\b[A-Z][A-Z0-9_]*(API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\b"
)
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|authorization|secret|token|password)\s*[:=]\s*[^,\s]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"\bsk-[A-Za-z0-9._\-]{8,}\b"),
)


class ApiException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def create_trace_id() -> str:
    return f"trace_{uuid4().hex}"


def get_trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    if isinstance(trace_id, str) and trace_id:
        return trace_id
    return create_trace_id()


def build_success_payload(data: Any, trace_id: str) -> dict[str, Any]:
    return ApiResponse[Any](data=data, error=None, trace_id=trace_id).model_dump(mode="json")


def build_error_payload(
    *,
    code: str,
    message: str,
    trace_id: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_message = redact_sensitive(message)
    error = ApiError(
        code=code,
        message=safe_message if isinstance(safe_message, str) else "Error",
        details=redact_sensitive(details or {}),
    )
    return ApiResponse[Any](data=None, error=error, trace_id=trace_id).model_dump(mode="json")


def success_response(
    data: Any,
    trace_id: str,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    return JSONResponse(
        content=build_success_payload(data=data, trace_id=trace_id),
        status_code=status_code,
        headers={TRACE_ID_HEADER: trace_id},
    )


def error_response(
    *,
    code: str,
    message: str,
    trace_id: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        content=build_error_payload(
            code=code,
            message=message,
            trace_id=trace_id,
            details=details,
        ),
        status_code=status_code,
        headers={TRACE_ID_HEADER: trace_id},
    )


def register_api_response_handlers(api: FastAPI) -> None:
    @api.middleware("http")
    async def trace_id_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.trace_id = _resolve_trace_id(request)
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = get_trace_id(request)
        return response

    api.add_exception_handler(ApiException, api_exception_handler)
    api.add_exception_handler(StarletteHTTPException, http_exception_handler)
    api.add_exception_handler(RequestValidationError, validation_exception_handler)
    api.add_exception_handler(Exception, unhandled_exception_handler)


async def api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
    return error_response(
        code=exc.code,
        message=exc.message,
        trace_id=get_trace_id(request),
        status_code=exc.status_code,
        details=exc.details,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == status.HTTP_404_NOT_FOUND else "HTTP_ERROR"
    message = "Resource not found" if exc.status_code == status.HTTP_404_NOT_FOUND else "HTTP error"
    return error_response(
        code=code,
        message=message,
        trace_id=get_trace_id(request),
        status_code=exc.status_code,
        details={"path": request.url.path},
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "loc": error.get("loc", ()),
            "msg": error.get("msg", "Invalid input"),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    return error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        trace_id=get_trace_id(request),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="Internal server error",
        trace_id=get_trace_id(request),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"path": request.url.path, "exception_type": exc.__class__.__name__},
    )


def redact_sensitive(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return "[REDACTED]"
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = redact_sensitive(item, depth + 1)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item, depth + 1) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive(item, depth + 1) for item in value]
    if isinstance(value, str):
        return _redact_string(value)
    return value


def _resolve_trace_id(request: Request) -> str:
    candidate = request.headers.get(TRACE_ID_HEADER)
    if candidate and _TRACE_ID_PATTERN.fullmatch(candidate):
        return candidate
    return create_trace_id()


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_string(value: str) -> str:
    redacted = _SENSITIVE_ENV_NAME_PATTERN.sub("[REDACTED]", value)
    for secret_value in _sensitive_env_values():
        redacted = redacted.replace(secret_value, "[REDACTED]")
    for pattern in _SENSITIVE_VALUE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _sensitive_env_values() -> set[str]:
    values: set[str] = set()
    for key, value in os.environ.items():
        if value and len(value) >= 4 and _is_sensitive_key(key):
            values.add(value)
    return values
