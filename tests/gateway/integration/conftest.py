from __future__ import annotations

import pytest

from medilink_ai.gateway import AICapability, AuthenticatedPrincipal, GatewayAuthorizationService, GatewayRequest
from medilink_ai.gateway.orchestration import GatewayOrchestrator
from medilink_ai.gateway.safety import AISafetyService

from .fakes import FakeContextService, FakeExecutor, FakePHIService


@pytest.fixture
def authorized_principal():
    return AuthenticatedPrincipal("doctor-001", "org-001", frozenset({"facility-001"}), frozenset({"clinical"}), frozenset({"DOCTOR"}), frozenset({"ai:use", "ai:knowledge:ask", "ai:patient_summary", "ai:documentation:draft", "patient:context:read"}))


@pytest.fixture
def other_facility_principal():
    return AuthenticatedPrincipal("doctor-002", "org-001", frozenset({"facility-002"}), frozenset({"clinical"}), frozenset({"DOCTOR"}), frozenset({"ai:use", "ai:patient_summary", "patient:context:read"}))


@pytest.fixture
def knowledge_request():
    return GatewayRequest(capability=AICapability.KNOWLEDGE_ASK, module="clinical", facility_id="facility-001", department_id="clinical", purpose="Understand an approved procedure", query="What is the pharmacy POS procedure?")


@pytest.fixture
def patient_summary_request():
    return GatewayRequest(capability=AICapability.PATIENT_SUMMARY, module="clinical", facility_id="facility-001", department_id="clinical", patient_id="patient-001", encounter_id="encounter-001", purpose="Prepare a clinical handover summary", query="Summarize the recent encounter.")


def make_orchestrator(*, context=None, phi=None, executor=None, audit=None, output_validator=None):
    return GatewayOrchestrator(GatewayAuthorizationService(), context or FakeContextService(), phi or FakePHIService(), AISafetyService(), executor or FakeExecutor(), output_validator=output_validator, audit_service=audit)
