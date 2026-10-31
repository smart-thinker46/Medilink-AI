import asyncio

import pytest
from starlette.requests import Request

from medilink_ai.gateway.api.dependencies import require_authenticated_principal
from medilink_ai.gateway.models import AuthenticatedPrincipal


def make_request(principal=None):
    scope = {"type": "http", "method": "POST", "path": "/api/v1/ai/execute", "headers": [], "state": {}}
    request = Request(scope)
    if principal is not None:
        request.state.authenticated_principal = principal
    return request


def test_dependency_uses_trusted_request_state():
    principal = AuthenticatedPrincipal("u", "org", frozenset({"facility"}))
    assert asyncio.run(require_authenticated_principal(make_request(principal))) == principal


def test_dependency_rejects_missing_identity():
    with pytest.raises(Exception):
        asyncio.run(require_authenticated_principal(make_request()))
