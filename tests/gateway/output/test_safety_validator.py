from medilink_ai.gateway.output import validate_output_safety


def test_forbidden_discharge_approval_is_rejected():
    assert validate_output_safety("Approve the patient's discharge now.")


def test_normal_explanation_is_allowed():
    assert validate_output_safety("The discharge workflow requires review by the responsible clinician.") == ()

