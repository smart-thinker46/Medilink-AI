"""Safety engine. First line = architecture (the AI has no write path at all). This module is the
second line: refuse command-style requests, then validate model output before anyone sees it."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

_VERBS = (r"prescribe|discharge|diagnose|approve|authori[sz]e|release|order|start|stop|discontinue|"
          r"change|alter|edit|delete|modify|post|override|transfuse|operate")
COMMAND_RE = re.compile(rf"^\s*(please\s+|can you\s+|could you\s+|go ahead and\s+)?({_VERBS})\b", re.I)
INJECTION_RE = re.compile(r"\b(ignore|disregard|forget)\b.{0,40}\b(instructions|rules|guardrails|policy)\b", re.I)
DIRECTIVE_RE = re.compile(
    r"\b(diagnosis is|diagnosed with|patient has (sepsis|pneumonia|malaria)|"
    r"you should (start|stop|give|administer|prescribe)|start (treatment|antibiotics|therapy)|"
    r"discontinue|prescribe)\b", re.I)
CITE_RE = re.compile(r"\[([SD]\d+)\]")

REFUSAL = ("Medilink AI is advisory only. It cannot prescribe, diagnose, discharge, approve, change records "
           "or override controls. Use the relevant Medilink module; I can summarise, explain or flag items for review.")


@dataclass
class Validation:
    ok: bool
    issues: list = field(default_factory=list)


def check_request(text: str) -> str | None:
    """Return a refusal message for command-style or injection requests, else None."""
    if COMMAND_RE.search(text) or INJECTION_RE.search(text):
        return REFUSAL
    return None


def validate_output(text: str, valid_ids: set, require_citations: bool) -> Validation:
    issues = []
    for m in DIRECTIVE_RE.finditer(text):
        issues.append(f"directive/diagnostic language: '{m.group(0)}'")
    for cid in CITE_RE.findall(text):
        if cid not in valid_ids:
            issues.append(f"unknown citation [{cid}]")
    if require_citations:
        for line in text.splitlines():
            if line.strip().startswith(("-", "•")) and not CITE_RE.search(line):
                issues.append(f"uncited statement: '{line.strip()[:60]}'")
    return Validation(not issues, issues)
