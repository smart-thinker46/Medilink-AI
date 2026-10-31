from typing import Protocol

from ..models import AuthenticatedPrincipal


class IdentityProvider(Protocol):
    async def authenticate(self, request) -> AuthenticatedPrincipal:
        """Return a principal only after trusted authentication succeeds."""
        ...
