import pytest

from medilink_ai.gateway.audit.hashing import AuditHashingError, hash_audit_reference, sha256_fingerprint


def test_patient_reference_is_hmac_hashed(monkeypatch):
    monkeypatch.setenv("MEDILINK_AUDIT_HMAC_KEY", "development-test-key-with-more-than-32-characters")
    result = hash_audit_reference("patient-001", reference_type="PATIENT")
    assert result and len(result) == 64 and result != "patient-001"


def test_same_reference_is_stable_and_type_scoped(monkeypatch):
    monkeypatch.setenv("MEDILINK_AUDIT_HMAC_KEY", "development-test-key-with-more-than-32-characters")
    assert hash_audit_reference("patient-001", reference_type="PATIENT") == hash_audit_reference("patient-001", reference_type="PATIENT")
    assert hash_audit_reference("patient-001", reference_type="PATIENT") != hash_audit_reference("patient-001", reference_type="ENCOUNTER")


def test_missing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("MEDILINK_AUDIT_HMAC_KEY", raising=False)
    with pytest.raises(AuditHashingError):
        hash_audit_reference("patient-001", reference_type="PATIENT")


def test_fingerprint_is_not_raw_content():
    assert sha256_fingerprint("sensitive prompt") != "sensitive prompt"

