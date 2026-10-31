class PHIProtectionError(Exception):
    """Base exception for PHI protection failures."""


class PHIPolicyError(PHIProtectionError):
    pass


class PHIValidationError(PHIProtectionError):
    pass


class PHIDataProviderUnavailableError(PHIProtectionError):
    pass


class PHIQueryInspectionError(PHIProtectionError):
    pass


class PHIDetectionError(PHIProtectionError):
    pass


class PHIMinimizationError(PHIProtectionError):
    pass


class PHIPolicyViolation(PHIProtectionError):
    pass
