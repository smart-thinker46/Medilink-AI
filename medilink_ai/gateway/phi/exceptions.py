class PHIProtectionError(Exception):
    """Base exception for PHI protection failures."""


class PHIDetectionError(PHIProtectionError):
    pass


class PHIMinimizationError(PHIProtectionError):
    pass


class PHIPolicyViolation(PHIProtectionError):
    pass
