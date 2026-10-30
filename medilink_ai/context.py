"""Context builder = AI-level data minimisation. Only authorised, purpose-relevant records are
read, identifiers are stripped, and every fact is numbered so output can cite it."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

PURPOSE_SECTIONS = {
    "clinical_summary": ["conditions", "allergies", "medications", "results", "encounters"],
    "note_draft": ["conditions", "allergies", "medications"],
}


class HMISReader(Protocol):
    """Read-only port into Medilink. There is deliberately no write method."""
    def get_patient_record(self, patient_id: str) -> dict: ...


@dataclass
class Source:
    id: str          # S1, S2 ...
    kind: str
    text: str
    record_ref: str  # id of the underlying HMIS record ("View source result")
    date: str = ""


@dataclass
class Context:
    patient_id: str
    purpose: str
    sources: list


class InMemoryHMIS:
    """Demo data only. Replace with a read-only Medilink adapter."""
    def __init__(self, records: dict):
        self.records = records

    def get_patient_record(self, patient_id: str) -> dict:
        return self.records[patient_id]


class ContextBuilder:
    def __init__(self, hmis: HMISReader):
        self.hmis = hmis

    def build(self, patient_id: str, purpose: str) -> Context:
        record = self.hmis.get_patient_record(patient_id)
        sources, n = [], 0
        for section in PURPOSE_SECTIONS[purpose]:
            for item in record.get(section, []):
                n += 1
                sources.append(Source(f"S{n}", section.rstrip("s"), item["text"], item["ref"], item.get("date", "")))
        # Name, phone, national ID, address are never copied into the prompt.
        return Context(patient_id, purpose, sources)
