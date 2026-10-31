from medilink_ai.gateway.phi import PHIDetector, PHIMinimizer


def test_phone_and_email_are_redacted():
    text = "Call +254712345678 or email patient@example.com."
    result = PHIMinimizer().minimize(text, PHIDetector().inspect(text))
    assert "+254712345678" not in result.protected_text
    assert "patient@example.com" not in result.protected_text
    assert "[PHONE_REDACTED]" in result.protected_text
    assert "[EMAIL_REDACTED]" in result.protected_text


def test_clean_text_is_unchanged():
    text = "Pharmacy POS reconciliation procedure."
    assert PHIMinimizer().minimize(text, PHIDetector().inspect(text)).protected_text == text

