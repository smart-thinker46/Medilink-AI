from __future__ import annotations

from .detector import PHIDetector
from .models import PHIInspectionResult


class PHIInspector:
    def __init__(self, detector: PHIDetector | None = None):
        self.detector = detector or PHIDetector()

    def inspect(self, text: str) -> PHIInspectionResult:
        return self.detector.inspect(text)
