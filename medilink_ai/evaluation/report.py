from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import EvaluationResult, EvaluationSummary
from .release_gate import ReleaseGateResult


def build_report(results: list[EvaluationResult], summary: EvaluationSummary, model: str = "unknown") -> dict:
    return {"model": model, "summary": asdict(summary), "results": [asdict(result) for result in results]}


def write_json_report(path: str | Path, results: list[EvaluationResult], summary: EvaluationSummary, model: str = "unknown") -> None:
    Path(path).write_text(json.dumps(build_report(results, summary, model), indent=2), encoding="utf-8")


def render_markdown_report(results: list[EvaluationResult], summary: EvaluationSummary, model: str = "unknown") -> str:
    lines = [f"# Medilink AI Evaluation Report — {model}", "", f"- Cases: {summary.total_cases}", f"- Pass rate: {summary.pass_rate:.1%}", f"- Retrieval relevance: {summary.retrieval_relevance:.1%}", f"- Citation validity: {summary.citation_validity:.1%}", f"- Authorization accuracy: {summary.authorization_accuracy:.1%}", f"- Safety accuracy: {summary.safety_accuracy:.1%}", f"- Gates: {'PASS' if summary.gates_passed else 'FAIL'}", f"- Release status: **{summary.release_status}**", "", "| Case | Severity | Actual | Passed | Latency (ms) |", "|---|---|---|---:|---:|"]
    lines.extend(f"| {result.case_id} | {result.severity} | {result.actual_behavior} | {'yes' if result.passed else 'no'} | {result.latency_ms:.1f} |" for result in results)
    if summary.gate_failures:
        lines.extend(["", "## Gate failures", *[f"- {failure}" for failure in summary.gate_failures]])
    return "\n".join(lines) + "\n"


def render_evaluation_report(
    results: list[EvaluationResult],
    release_gate: ReleaseGateResult,
    model: str = "unknown",
    summary: EvaluationSummary | None = None,
) -> str:
    """Render the terminal-friendly report with the explicit release gate."""
    if summary is None:
        summary = __import__("medilink_ai.evaluation.metrics", fromlist=["summarize_results"]).summarize_results(results, [])
    lines = ["", "=" * 60, f"MEDILINK AI EVALUATION REPORT — {model}", "=" * 60, "", f"Total cases: {summary.total_cases}", f"Passed: {summary.passed_cases}", f"Pass rate: {summary.pass_rate:.1%}", f"Authorization: {summary.authorization_accuracy:.1%}", f"Safety: {summary.safety_accuracy:.1%}", f"Citations: {summary.citation_validity:.1%}", "", f"Release: {'PASS' if release_gate.passed else 'BLOCKED'}"]
    if release_gate.reasons:
        lines.extend(["", "Failures:", *[f"- {reason}" for reason in release_gate.reasons]])
    return "\n".join(lines) + "\n"
