class SafetyClassificationError(Exception):
    """Base exception for safety-classification failures."""


class SafetyPolicyViolation(SafetyClassificationError):
    pass


class SafetyClassificationUnavailable(SafetyClassificationError):
    pass
