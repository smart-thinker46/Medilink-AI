from medilink_ai.gateway.identity.claims import IdentityClaims


def test_claims_normalize_common_provider_names():
    claims = IdentityClaims.from_mapping({
        "sub": " doctor-001 ",
        "tenant_id": "org-001",
        "facility_id": "facility-001",
        "department_id": "clinical",
        "role": "DOCTOR",
        "permission": ["ai:use"],
        "classification": "internal",
    })
    assert claims.subject_id == "doctor-001"
    assert claims.organization_id == "org-001"
    assert claims.facility_ids == frozenset({"facility-001"})
    assert claims.classification_level == "INTERNAL"
