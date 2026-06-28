"""Unified error envelope. See docs/api/README.md."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .ids import gen_id

# code -> HTTP status
_CODE_STATUS = {
    "invalid_argument": 400,
    "unauthenticated": 401,
    "permission_denied": 403,
    "not_found": 404,
    "conflict": 409,
    "rate_limited": 429,
    "internal": 500,
}
_STATUS_CODE = {v: k for k, v in _CODE_STATUS.items()}


class APIError(Exception):
    """Raise to return a structured error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)

    @property
    def status_code(self) -> int:
        return _CODE_STATUS.get(self.code, 500)


def _envelope(
    request: Request,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or gen_id("req", 6)
    body: Dict[str, Any] = {"code": code, "message": message, "request_id": request_id}
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content={"error": body})


def install_error_handlers(app) -> None:
    @app.exception_handler(APIError)
    async def _api_error(request: Request, exc: APIError):  # noqa: ANN202
        return _envelope(request, exc.code, exc.message, exc.details, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):  # noqa: ANN202
        return _envelope(
            request,
            "invalid_argument",
            "Request validation failed",
            {"errors": exc.errors()},
            400,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):  # noqa: ANN202
        code = _STATUS_CODE.get(exc.status_code, "internal")
        return _envelope(request, code, str(exc.detail), None, exc.status_code)
