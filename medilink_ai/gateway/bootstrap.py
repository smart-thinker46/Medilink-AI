from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayDependencies:
    authorization_service: object
    context_service: object
    phi_service: object
    safety_service: object
    executor: object
    output_validator: object
    audit_service: object

