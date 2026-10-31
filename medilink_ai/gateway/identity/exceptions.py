class IdentityError(Exception):
    """Base exception for identity integration."""


class AuthenticationError(IdentityError):
    pass


class InvalidIdentityError(IdentityError):
    pass


class IdentityProviderUnavailableError(IdentityError):
    pass
