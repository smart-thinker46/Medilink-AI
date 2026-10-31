from medilink_ai.gateway.output import validate_output_phi


def test_possible_phone_number_is_detected():
    assert validate_output_phi("Contact the patient at 0712345678.")


def test_normal_text_has_no_phi_pattern():
    assert validate_output_phi("The pharmacy opens at 08:00.") == ()

