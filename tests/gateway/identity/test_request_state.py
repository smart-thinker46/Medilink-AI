import asyncio
import pytest
from starlette.requests import Request

from medilink_ai.gateway.identity.exceptions import AuthenticationError, InvalidIdentityError
from medilink_ai.gateway.identity.request_state import RequestStateIdentityProvider
from medilink_ai.gateway.models import AuthenticatedPrincipal


def create_request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/ai/test", "headers": [], "query_string": b""})


def test_missing_identity_is_rejected():
    with pytest.raises(AuthenticationError):
        asyncio.run(RequestStateIdentityProvider().authenticate(create_request()))


def test_request_body_or_headers_are_not_trusted():
    request = create_request()
    request.scope["headers"] = [(b"x-user-id", b"admin"), (b"x-role", b"SYSTEM_ADMIN")]
    with pytest.raises(AuthenticationError):
        asyncio.run(RequestStateIdentityProvider().authenticate(request))


def test_invalid_state_identity_is_rejected():
    request = create_request()
    request.state.authenticated_principal = {"subject_id": "user", "organization_id": "org"}
    with pytest.raises(InvalidIdentityError):
        asyncio.run(RequestStateIdentityProvider().authenticate(request))


def test_incomplete_identity_is_rejected():
    request = create_request()
    request.state.authenticated_principal = AuthenticatedPrincipal("user", "org")
    with pytest.raises(InvalidIdentityError):
        asyncio.run(RequestStateIdentityProvider().authenticate(request))


def test_valid_trusted_identity_is_returned():
    request = create_request()
    principal = AuthenticatedPrincipal("user", "org", facility_ids=frozenset({"facility-1"}))
    request.state.authenticated_principal = principal
    assert asyncio.run(RequestStateIdentityProvider().authenticate(request)) is principal
