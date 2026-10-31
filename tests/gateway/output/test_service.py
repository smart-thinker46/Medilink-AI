from medilink_ai.gateway.output import AIOutputValidationService, OutputValidationStatus


def valid_output(**overrides):
    value = {"answer": "Pharmacy POS handles retail sales.", "status": "ANSWERED", "citations": [{"source_id": "S1", "claim": "Retail sales"}], "limitations": [], "human_review_required": False}
    value.update(overrides)
    return value


def test_valid_output_passes():
    result = AIOutputValidationService().validate(raw_output=valid_output(), allowed_source_ids={"S1"})
    assert result.status == OutputValidationStatus.VALID
    assert result.response is not None


def test_invalid_citation_blocks_delivery():
    result = AIOutputValidationService().validate(raw_output=valid_output(citations=[{"source_id": "S99", "claim": "No"}]), allowed_source_ids={"S1"})
    assert result.status == OutputValidationStatus.INVALID
    assert result.response is None


def test_forbidden_output_is_blocked():
    result = AIOutputValidationService().validate(raw_output=valid_output(answer="Approve the patient's discharge."), allowed_source_ids={"S1"})
    assert result.status == OutputValidationStatus.BLOCKED
    assert result.response is None


def test_human_review_is_authoritative():
    result = AIOutputValidationService().validate(raw_output=valid_output(), allowed_source_ids={"S1"}, human_review_required=True)
    assert result.status == OutputValidationStatus.REVIEW_REQUIRED
    assert result.response and result.response.human_review_required is True


def test_malformed_output_is_rejected():
    result = AIOutputValidationService().validate(raw_output={"answer": "x", "status": "ANSWERED", "unexpected": True}, allowed_source_ids=set())
    assert result.status == OutputValidationStatus.INVALID
