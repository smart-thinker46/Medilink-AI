"""Translate trusted Medilink claims into the gateway principal."""
from __future__ import annotations

from .claims import IdentityClaims
from .validation import validate_identity_claims
from ..models import AuthenticatedPrincipal


class MedilinkIdentityAdapter:
    """Deterministic adapter; authentication remains owned by Medilink."""

    def adapt(self, claims: IdentityClaims) -> AuthenticatedPrincipal:
        validate_identity_claims(claims)
        return AuthenticatedPrincipal(
            subject_id=claims.subject_id,
            organization_id=claims.organization_id,
            facility_ids=claims.facility_ids,
            department_ids=claims.department_ids,
            roles=claims.roles,
            permissions=claims.permissions,
            classification_level=claims.classification_level,
            is_service_account=claims.is_service_account,
        )
