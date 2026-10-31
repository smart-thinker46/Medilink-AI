from medilink_ai.gateway.phi import PHIDetector, PHILevel, PHIType


def test_detector_detects_kenyan_phone_number():
    result = PHIDetector().inspect("Contact the patient at +254712345678.")
    assert result.contains_phi
    assert result.highest_level == PHILevel.MODERATE
    assert any(match.phi_type == PHIType.PHONE for match in result.matches)


def test_detector_detects_email_and_structured_identifiers():
    result = PHIDetector().inspect("Email: patient@example.com; MRN: MRN-001234; National ID: 12345678")
    assert {match.phi_type for match in result.matches} >= {PHIType.EMAIL, PHIType.MEDICAL_RECORD_NUMBER, PHIType.NATIONAL_ID}

