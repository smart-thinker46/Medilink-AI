class ContextIntegrationError(Exception):
    """Base exception for authoritative HMIS context integration."""


class ContextNotFoundError(ContextIntegrationError):
    pass


class ContextAuthorizationError(ContextIntegrationError):
    pass


class ContextValidationError(ContextIntegrationError):
    """A supplied context failed an ownership or access rule."""

    def __init__(self, message: str, reason_code: str = "CONTEXT_VALIDATION_FAILED"):
        super().__init__(message)
        self.reason_code = reason_code


class ContextProviderUnavailableError(ContextIntegrationError):
    """The authoritative HMIS context service could not be queried."""


class ContextAuthorizationUnavailableError(ContextIntegrationError):
    """The authoritative patient/encounter access check could not complete."""
