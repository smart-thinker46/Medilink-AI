import pytest

from medilink_ai.gateway.identity.claims import IdentityClaims
from medilink_ai.gateway.identity.exceptions import InvalidIdentityError
from medilink_ai.gateway.identity.validation import validate_identity_claims


def claims(**changes):
    values = dict(
        subject_id="doctor-001",
        organization_id="org-001",
        facility_ids=frozenset({"facility-001"}),
        department_ids=frozenset({"clinical"}),
        roles=frozenset({"DOCTOR"}),
        permissions=frozenset({"ai:use"}),
    )
    values.update(changes)
    return IdentityClaims(**values)


@pytest.mark.parametrize("field", ["subject_id", "organization_id"])
def test_required_identity_fields_are_rejected(field):
    with pytest.raises(InvalidIdentityError):
        validate_identity_claims(claims(**{field: "  "}))


@pytest.mark.parametrize("field", ["facility_ids", "roles", "permissions"])
def test_empty_security_membership_is_rejected(field):
    with pytest.raises(InvalidIdentityError):
        validate_identity_claims(claims(**{field: frozenset()})) if field == "facility_ids" else validate_identity_claims(claims(**{field: frozenset({""})}))


def test_valid_claims_are_returned_unchanged():
    value = claims()
    assert validate_identity_claims(value) is value
