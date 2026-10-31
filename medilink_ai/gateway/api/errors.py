from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def gateway_error_response(*, request: Request, status_code: int, code: str, message: str, request_id: str | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"request_id": request_id, "error": code, "message": message})


def map_gateway_exception(*, request: Request, exc: Exception, request_id: str | None = None) -> JSONResponse:
    # Deliberately do not expose exception text, stack traces, paths, or provider details.
    from ..identity.exceptions import AuthenticationError, InvalidIdentityError

    if isinstance(exc, (AuthenticationError, InvalidIdentityError)):
        return gateway_error_response(request=request, status_code=401, code="AUTHENTICATION_REQUIRED", message="Authentication required.", request_id=request_id)
    if isinstance(exc, PermissionError):
        return gateway_error_response(request=request, status_code=403, code="ACCESS_DENIED", message="Access denied.", request_id=request_id)
    return gateway_error_response(request=request, status_code=503, code="AI_GATEWAY_UNAVAILABLE", message="The AI gateway could not complete this request.", request_id=request_id)
