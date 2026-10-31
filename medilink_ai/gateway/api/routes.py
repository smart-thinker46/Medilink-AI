from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..models import AuthenticatedPrincipal
from ..schemas import GatewayRequest
from .dependencies import require_authenticated_principal
from .errors import gateway_error_response, map_gateway_exception
from .responses import AIExecuteResponse, GatewayStageResponse


router = APIRouter(prefix="/api/v1/ai", tags=["AI Gateway"])


def _response(payload: GatewayRequest, result) -> AIExecuteResponse:
    return AIExecuteResponse(
        request_id=result.request_id,
        status=result.status.value if hasattr(result.status, "value") else str(result.status),
        capability=payload.capability.value if hasattr(payload.capability, "value") else str(payload.capability),
        response=result.output,
        human_review_required=result.human_review_required,
        reason_codes=list(result.reason_codes),
        stages=[GatewayStageResponse(stage=stage.stage.value if hasattr(stage.stage, "value") else str(stage.stage), status=stage.status.value if hasattr(stage.status, "value") else str(stage.status), reason_codes=list(stage.reason_codes), duration_ms=stage.duration_ms) for stage in result.stages],
    )


@router.get("/health")
async def ai_gateway_health():
    return {"status": "ok", "service": "medilink-ai-gateway"}


@router.post("/execute", response_model=AIExecuteResponse)
async def execute_ai(payload: GatewayRequest, request: Request, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal)):
    request_id = str(payload.request_id)
    gateway = getattr(request.app.state, "ai_gateway", None)
    if gateway is None:
        return gateway_error_response(request=request, status_code=503, code="AI_GATEWAY_NOT_CONFIGURED", message="The AI gateway is not configured.", request_id=request_id)
    try:
        result = await gateway.execute(principal=principal, request=payload)
        return _response(payload, result)
    except Exception as exc:
        return map_gateway_exception(request=request, exc=exc, request_id=request_id)
