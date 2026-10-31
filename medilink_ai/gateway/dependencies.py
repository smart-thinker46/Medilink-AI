from fastapi import HTTPException, Request, status

from .identity import AuthenticationError, InvalidIdentityError, IdentityProviderUnavailableError, RequestStateIdentityProvider
from .models import AuthenticatedPrincipal

identity_provider = RequestStateIdentityProvider()


async def get_authenticated_principal(request: Request) -> AuthenticatedPrincipal:
    try:
        provider = getattr(request.app.state, "identity_provider", identity_provider)
    except (AttributeError, KeyError):
        # Unit-level requests may not have an ASGI app scope; retain the
        # provider-neutral request-state boundary in that case.
        provider = identity_provider
    try:
        return await provider.authenticate(request)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.") from exc
    except InvalidIdentityError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated identity is invalid.") from exc
    except IdentityProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Identity provider unavailable.") from exc
