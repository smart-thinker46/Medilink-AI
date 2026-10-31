from medilink_ai.gateway.safety import AIActionType, SafetyActionClassifier


def test_critical_actions_are_checked_before_safe_actions():
    classifier = SafetyActionClassifier()
    assert classifier.classify("Summarize the patient and approve discharge") == AIActionType.APPROVE


def test_classifier_detects_critical_actions():
    classifier = SafetyActionClassifier()
    assert classifier.classify("Authorize this patient's medication") == AIActionType.AUTHORIZE
    assert classifier.classify("Modify the patient's billing balance") == AIActionType.MODIFY
    assert classifier.classify("Go ahead and complete the discharge process") == AIActionType.EXECUTE


def test_classifier_detects_safe_and_review_actions():
    classifier = SafetyActionClassifier()
    assert classifier.classify("Explain the pharmacy procedure") == AIActionType.EXPLAIN
    assert classifier.classify("Draft a clinical note") == AIActionType.DRAFT
    assert classifier.classify("Recommend next steps") == AIActionType.RECOMMEND

