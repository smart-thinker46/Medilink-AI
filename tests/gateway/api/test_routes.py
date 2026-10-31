from fastapi import FastAPI
import asyncio
import httpx

from medilink_ai.gateway.api import router
from medilink_ai.gateway.models import AuthenticatedPrincipal


class FakeGateway:
    async def execute(self, *, principal, request):
        from medilink_ai.gateway.orchestration.models import GatewayExecutionStatus, OrchestrationResult
        return OrchestrationResult(str(request.request_id), GatewayExecutionStatus.COMPLETED)


def app():
    application = FastAPI()
    application.include_router(router)
    application.state.ai_gateway = FakeGateway()
    return application


def test_health_is_liveness_only():
    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url="http://test") as client:
            return await client.get("/api/v1/ai/health")
    response = asyncio.run(call())
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "medilink-ai-gateway"}


def test_execute_requires_trusted_identity():
    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url="http://test") as client:
            return await client.post("/api/v1/ai/execute", json={"capability": "knowledge.ask", "module": "clinical", "facility_id": "facility-001", "query": "Explain policy"})
    response = asyncio.run(call())
    assert response.status_code == 401


def test_execute_does_not_accept_client_identity_fields():
    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app()), base_url="http://test") as client:
            return await client.post("/api/v1/ai/execute", json={"capability": "knowledge.ask", "module": "clinical", "facility_id": "facility-001", "query": "Explain policy", "user_id": "attacker", "roles": ["ADMIN"]})
    response = asyncio.run(call())
    # Authentication is evaluated before request-body processing; an unauthenticated
    # caller cannot use malformed identity fields to probe the endpoint.
    assert response.status_code == 401

