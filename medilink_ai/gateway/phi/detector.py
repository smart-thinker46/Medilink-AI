from __future__ import annotations

import re

from .models import PHIInspectionResult, PHILevel, PHIMatch, PHIType


class PHIDetector:
    """Conservative local detector; structured HMIS metadata remains authoritative."""

    PATTERNS = (
        (PHIType.PHONE, PHILevel.MODERATE, re.compile(r"\b(?:\+254|254|0)7\d{8}\b|\b(?:\+254|254|0)1\d{8}\b")),
        (PHIType.EMAIL, PHILevel.MODERATE, re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
        (PHIType.MEDICAL_RECORD_NUMBER, PHILevel.HIGH, re.compile(r"\b(?:MRN|medical\s+record(?:\s+number)?)\s*[:#-]?\s*[A-Za-z0-9][A-Za-z0-9-]*", re.I)),
        (PHIType.PATIENT_ID, PHILevel.HIGH, re.compile(r"\bpatient[-_ ]?id\s*[:#-]?\s*[A-Za-z0-9][A-Za-z0-9-]*", re.I)),
        (PHIType.ENCOUNTER_ID, PHILevel.HIGH, re.compile(r"\b(?:encounter|admission|visit)[-_ ]?(?:id|number)?\s*[:#-]?\s*[A-Za-z0-9][A-Za-z0-9-]*", re.I)),
        (PHIType.NATIONAL_ID, PHILevel.RESTRICTED, re.compile(r"\b(?:national\s+id|id\s+number|identity\s+number)\s*[:#-]?\s*[A-Za-z0-9-]{5,}\b", re.I)),
        (PHIType.PASSPORT, PHILevel.RESTRICTED, re.compile(r"\bpassport(?:\s+number)?\s*[:#-]?\s*[A-Za-z0-9-]{5,}\b", re.I)),
        (PHIType.DATE_OF_BIRTH, PHILevel.HIGH, re.compile(r"\b(?:date\s+of\s+birth|dob)\s*[:#-]?\s*\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b", re.I)),
    )

    def inspect(self, text: str) -> PHIInspectionResult:
        if not isinstance(text, str):
            raise TypeError("PHI inspection requires text")
        matches: list[PHIMatch] = []
        for phi_type, level, pattern in self.PATTERNS:
            for found in pattern.finditer(text):
                matches.append(PHIMatch(phi_type, level, found.start(), found.end(), found.group(0)))
        # Keep deterministic, non-overlapping matches. More specific patterns win.
        priority = {level: index for index, level in enumerate(PHILevel)}
        selected: list[PHIMatch] = []
        for match in sorted(matches, key=lambda item: (item.start, -priority[item.level], -(item.end - item.start))):
            if any(match.start < prior.end and prior.start < match.end for prior in selected):
                continue
            selected.append(match)
        return PHIInspectionResult(tuple(sorted(selected, key=lambda item: item.start)))
