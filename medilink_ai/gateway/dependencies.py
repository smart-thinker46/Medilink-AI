from fastapi import HTTPException, Request, status

from .identity import AuthenticationError, InvalidIdentityError, RequestStateIdentityProvider
from .models import AuthenticatedPrincipal

identity_provider = RequestStateIdentityProvider()


async def get_authenticated_principal(request: Request) -> AuthenticatedPrincipal:
    try:
        return await identity_provider.authenticate(request)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.") from exc
    except InvalidIdentityError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated identity is invalid.") from exc
