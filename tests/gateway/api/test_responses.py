from medilink_ai.gateway.api.responses import AIExecuteResponse, GatewayStageResponse


def test_response_model_is_strict_and_serializable():
    response = AIExecuteResponse(request_id="r1", status="COMPLETED", capability="knowledge.ask", stages=[GatewayStageResponse(stage="AUTHORIZATION", status="COMPLETED")])
    assert response.model_dump()["request_id"] == "r1"
