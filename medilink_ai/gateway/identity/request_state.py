from fastapi import Request

from ..models import AuthenticatedPrincipal
from .exceptions import AuthenticationError, InvalidIdentityError
from .validation import validate_identity_claims
from .claims import IdentityClaims


class RequestStateIdentityProvider:
    """Read a principal attached by trusted upstream authentication middleware."""

    async def authenticate(self, request: Request) -> AuthenticatedPrincipal:
        principal = getattr(request.state, "authenticated_principal", None)
        if principal is None:
            raise AuthenticationError("Authentication is required.")
        if not isinstance(principal, AuthenticatedPrincipal):
            raise InvalidIdentityError("Authenticated principal is invalid.")
        validate_identity_claims(IdentityClaims(
            subject_id=principal.subject_id,
            organization_id=principal.organization_id,
            facility_ids=principal.facility_ids,
            department_ids=principal.department_ids,
            roles=principal.roles,
            permissions=principal.permissions,
            classification_level=principal.classification_level,
            is_service_account=principal.is_service_account,
        ))
        return principal
