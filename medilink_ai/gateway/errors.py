class GatewayError(Exception):
    """Base exception for Gateway operations."""


class GatewayAuthenticationError(GatewayError):
    pass


class GatewayAuthorizationError(GatewayError):
    pass


class GatewayContextError(GatewayError):
    pass


class GatewaySafetyError(GatewayError):
    pass


class GatewayRateLimitError(GatewayError):
    pass


class GatewayProviderError(GatewayError):
    pass


class GatewayValidationError(GatewayError):
    pass
