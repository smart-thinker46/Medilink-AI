from fastapi import Request

from ..models import AuthenticatedPrincipal
from .exceptions import AuthenticationError, InvalidIdentityError


class RequestStateIdentityProvider:
    """Read a principal attached by trusted upstream authentication middleware."""

    async def authenticate(self, request: Request) -> AuthenticatedPrincipal:
        principal = getattr(request.state, "authenticated_principal", None)
        if principal is None:
            raise AuthenticationError("Authentication is required.")
        if not isinstance(principal, AuthenticatedPrincipal):
            raise InvalidIdentityError("Authenticated principal is invalid.")
        if not principal.subject_id or not principal.organization_id:
            raise InvalidIdentityError("Authenticated principal is incomplete.")
        if not principal.facility_ids:
            raise InvalidIdentityError("Authenticated principal has no facility access.")
        return principal
