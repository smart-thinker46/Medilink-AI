from medilink_ai.gateway.identity.adapter import MedilinkIdentityAdapter
from medilink_ai.gateway.identity.claims import IdentityClaims


def test_adapter_creates_canonical_principal_without_client_authority():
    principal = MedilinkIdentityAdapter().adapt(IdentityClaims(
        subject_id="doctor-001",
        organization_id="org-001",
        facility_ids=frozenset({"facility-001"}),
        department_ids=frozenset({"clinical"}),
        roles=frozenset({"DOCTOR"}),
        permissions=frozenset({"ai:use"}),
        is_service_account=True,
    ))
    assert principal.subject_id == "doctor-001"
    assert principal.organization_id == "org-001"
    assert principal.permissions == frozenset({"ai:use"})
    assert principal.is_service_account is True
