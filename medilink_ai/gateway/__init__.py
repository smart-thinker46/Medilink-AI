"""Gateway policy primitives and the legacy orchestration gateway.

The project historically had ``medilink_ai/gateway.py`` as the runtime
orchestrator.  This package now owns the Step 6 policy/context components;
load the legacy class under a private module name so existing app imports
remain compatible while the two layers are migrated independently.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


_legacy_name = "medilink_ai._legacy_gateway"
_legacy_path = Path(__file__).resolve().parent.parent / "gateway.py"
_legacy_spec = spec_from_file_location(_legacy_name, _legacy_path)
if _legacy_spec and _legacy_spec.loader:
    _legacy_module = module_from_spec(_legacy_spec)
    sys.modules.setdefault(_legacy_name, _legacy_module)
    _legacy_spec.loader.exec_module(_legacy_module)
    Gateway = _legacy_module.Gateway

from .models import AICapability, AIRiskLevel, AuthenticatedPrincipal, GatewayDecision, GatewayDecisionStatus, GatewayExecutionContext
from .policy import authorize_gateway_request
from .schemas import GatewayRequest
from .authorization_service import GatewayAuthorizationService
from .capability_registry import CapabilityPolicy, get_capability_policy
from .context import ContextValidationService, ValidatedRequestContext
from .phi import PHIProtectionService
from .safety import AISafetyService
from .orchestration import GatewayOrchestrator
from .routing import ModelRouter, ModelRegistry, RoutedAIExecutor
from .output import AIOutputValidationService
from .api import router as api_router

__all__ = ["AICapability", "AIRiskLevel", "AuthenticatedPrincipal", "GatewayDecision", "GatewayDecisionStatus", "GatewayExecutionContext", "GatewayRequest", "authorize_gateway_request", "GatewayAuthorizationService", "CapabilityPolicy", "get_capability_policy", "ContextValidationService", "ValidatedRequestContext", "PHIProtectionService", "AISafetyService", "GatewayOrchestrator", "ModelRouter", "ModelRegistry", "RoutedAIExecutor", "AIOutputValidationService", "api_router"]
