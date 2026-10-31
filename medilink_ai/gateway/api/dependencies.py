from __future__ import annotations

from fastapi import Request

from ..dependencies import get_authenticated_principal
from ..models import AuthenticatedPrincipal


async def require_authenticated_principal(request: Request) -> AuthenticatedPrincipal:
    return await get_authenticated_principal(request)
