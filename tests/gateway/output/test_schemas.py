import pytest
from pydantic import ValidationError

from medilink_ai.gateway.output import GatewayAIResponse


def test_valid_gateway_response():
    response = GatewayAIResponse.model_validate({"answer": "Pharmacy POS handles retail sales.", "status": "ANSWERED"})
    assert response.answer


def test_unknown_output_field_is_rejected():
    with pytest.raises(ValidationError):
        GatewayAIResponse.model_validate({"answer": "Test", "status": "ANSWERED", "execute_transaction": True})

