"""Identity provider construction and production configuration guards."""
from __future__ import annotations

import os

from .exceptions import IdentityProviderUnavailableError
from .request_state import RequestStateIdentityProvider


def ensure_production_identity_configuration() -> None:
    """Fail fast when production has no explicitly selected provider."""
    environment = os.getenv("MEDILINK_ENVIRONMENT", os.getenv("MEDILINK_ENV", "development")).strip().lower()
    if environment == "production" and not os.getenv("MEDILINK_IDENTITY_PROVIDER", "").strip():
        raise IdentityProviderUnavailableError("Production identity provider is not configured.")


def create_identity_provider():
    """Return the configured provider boundary.

    Request-state integration is the only provider implemented until the real
    Medilink authentication protocol is documented.  Trusted middleware must
    populate ``request.state.authenticated_principal`` first.
    """
    ensure_production_identity_configuration()
    provider = os.getenv("MEDILINK_IDENTITY_PROVIDER", "request_state").strip().lower()
    if provider == "request_state":
        return RequestStateIdentityProvider()
    raise IdentityProviderUnavailableError(f"Unsupported identity provider: {provider}.")
