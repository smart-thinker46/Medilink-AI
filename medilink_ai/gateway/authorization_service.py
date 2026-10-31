from .models import AuthenticatedPrincipal, GatewayDecision
from .policy import authorize_gateway_request
from .schemas import GatewayRequest


class GatewayAuthorizationService:
    def authorize(self, principal: AuthenticatedPrincipal, request: GatewayRequest, *, patient_access_verified: bool = False, encounter_access_verified: bool = False) -> GatewayDecision:
        return authorize_gateway_request(principal, request, patient_access_verified=patient_access_verified, encounter_access_verified=encounter_access_verified)
