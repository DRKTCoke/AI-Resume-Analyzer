import uuid
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


HTTP_ERROR_CODES = {
    400: "bad_request",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
}


def get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return request_id
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    return request_id


def error_response(
    request: Request,
    status_code: int,
    message: str,
    *,
    code: str | None = None,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "error": {
            "code": code or HTTP_ERROR_CODES.get(status_code, "internal_error"),
            "message": message,
            "request_id": get_request_id(request),
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload), headers=headers)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Request failed"
    details = None if isinstance(detail, str) else detail
    return error_response(
        request,
        exc.status_code,
        message,
        code=HTTP_ERROR_CODES.get(exc.status_code),
        details=details,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request,
        422,
        "Request validation failed",
        code="validation_error",
        details=exc.errors(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        request,
        500,
        "Internal server error",
        code="internal_error",
    )
