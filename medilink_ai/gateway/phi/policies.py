from __future__ import annotations

from .exceptions import PHIPolicyError
from .models import PHIProtectionPolicy

PHI_POLICIES = {
    "knowledge.ask": PHIProtectionPolicy("knowledge.ask", frozenset(), frozenset(), frozenset({"GENERAL_KNOWLEDGE"}), maximum_records=0),
    "patient.summary": PHIProtectionPolicy("patient.summary", frozenset({"age_band", "sex_at_birth", "patient_status"}), frozenset({"encounter_date", "encounter_type", "department", "diagnoses", "allergies", "active_medications"}), frozenset({"PATIENT_SUMMARY"}), requires_patient_context=True, requires_encounter_context=True, human_review_required=True),
    "documentation.draft": PHIProtectionPolicy("documentation.draft", frozenset({"age_band", "sex_at_birth", "patient_status"}), frozenset({"encounter_date", "encounter_type", "department", "diagnoses", "allergies", "active_medications", "clinical_observations", "vitals"}), frozenset({"DOCUMENTATION_DRAFT"}), requires_patient_context=True, requires_encounter_context=True, human_review_required=True),
    "operational.insights": PHIProtectionPolicy("operational.insights", frozenset(), frozenset(), frozenset({"OPERATIONAL_INSIGHTS"}), maximum_records=0),
}


def get_phi_policy(capability: str) -> PHIProtectionPolicy:
    key = capability.value if hasattr(capability, "value") else str(capability)
    policy = PHI_POLICIES.get(key)
    if policy is None:
        raise PHIPolicyError("No PHI protection policy is registered for this capability.")
    return policy
