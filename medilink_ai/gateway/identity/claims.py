"""Provider-neutral claims received from trusted Medilink Security adapters.

This module deliberately does not decode JWTs, cookies, or request headers.
Those are owned by Medilink Security.  Concrete adapters translate their
verified result into :class:`IdentityClaims`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .exceptions import InvalidIdentityError


def _values(value: Any, field: str) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        value = [value]
    try:
        values = list(value)
    except TypeError as exc:
        raise InvalidIdentityError(f"Identity field '{field}' is invalid.") from exc
    if any(not isinstance(item, str) for item in values):
        raise InvalidIdentityError(f"Identity field '{field}' is invalid.")
    return frozenset(item.strip() for item in values)


@dataclass(frozen=True)
class IdentityClaims:
    """Normalized, but not yet validated, claims from Medilink Security."""

    subject_id: str
    organization_id: str
    facility_ids: frozenset[str]
    department_ids: frozenset[str]
    roles: frozenset[str]
    permissions: frozenset[str]
    classification_level: str = "INTERNAL"
    is_service_account: bool = False

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "IdentityClaims":
        """Normalize common upstream claim names at one boundary.

        This accepts a verified claim mapping supplied by an adapter, not an
        arbitrary browser payload.  Unknown keys are ignored so providers can
        carry unrelated claims without leaking them into the gateway.
        """
        if not isinstance(values, Mapping):
            raise InvalidIdentityError("Authenticated claims are invalid.")

        def first(*names: str) -> Any:
            for name in names:
                if name in values and values[name] is not None:
                    return values[name]
            return None

        subject = first("subject_id", "sub", "user_id", "uid", "username")
        organization = first("organization_id", "org_id", "tenant_id")
        classification = first("classification_level", "classification") or "INTERNAL"
        if not isinstance(subject, str) or not isinstance(organization, str):
            raise InvalidIdentityError("Authenticated identity is missing subject or organization.")
        if not isinstance(classification, str):
            raise InvalidIdentityError("Identity classification is invalid.")
        service = first("is_service_account", "service_account")
        if service is None:
            service = False
        if not isinstance(service, bool):
            raise InvalidIdentityError("Identity service-account flag is invalid.")
        return cls(
            subject_id=subject.strip(),
            organization_id=organization.strip(),
            facility_ids=_values(first("facility_ids", "facilities", "facility_id"), "facilities"),
            department_ids=_values(first("department_ids", "departments", "department_id"), "departments"),
            roles=_values(first("roles", "role"), "roles"),
            permissions=_values(first("permissions", "permission"), "permissions"),
            classification_level=classification.strip().upper(),
            is_service_account=service,
        )
