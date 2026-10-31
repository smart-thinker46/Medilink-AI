"""Fail-closed validation for normalized identity claims."""
from __future__ import annotations

from .claims import IdentityClaims
from .exceptions import InvalidIdentityError


def _non_blank(values: frozenset[str], label: str) -> None:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise InvalidIdentityError(f"Authenticated identity contains an invalid {label}.")


def validate_identity_claims(claims: IdentityClaims) -> IdentityClaims:
    if not isinstance(claims, IdentityClaims):
        raise InvalidIdentityError("Authenticated claims are invalid.")
    if not isinstance(claims.subject_id, str) or not claims.subject_id.strip():
        raise InvalidIdentityError("Authenticated identity has no subject.")
    if not isinstance(claims.organization_id, str) or not claims.organization_id.strip():
        raise InvalidIdentityError("Authenticated identity has no organization.")
    if not claims.facility_ids:
        raise InvalidIdentityError("Authenticated identity has no facility access.")
    _non_blank(claims.facility_ids, "facility")
    _non_blank(claims.department_ids, "department")
    _non_blank(claims.roles, "role")
    _non_blank(claims.permissions, "permission")
    if not isinstance(claims.classification_level, str) or not claims.classification_level.strip():
        raise InvalidIdentityError("Authenticated identity has no classification.")
    if not isinstance(claims.is_service_account, bool):
        raise InvalidIdentityError("Authenticated identity has an invalid service-account flag.")
    return claims
