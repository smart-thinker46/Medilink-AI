from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import os

from ..db.session import get_session_factory
from ..knowledge.assistant_service import HospitalKnowledgeAssistant
from .dataset import load_evaluation_dataset
from .config import ensure_evaluation_environment
from .release_gate import evaluate_release_gate
from .report import render_evaluation_report, render_markdown_report, write_json_report
from .runner import EvaluationRunner
from .fixtures import load_controlled_fixtures
from .db import get_evaluation_session_factory
from .retrieval_runner import run_retrieval_evaluation, summarize_retrieval_results
from .benchmark_models import build_manifest, write_manifest


async def run(args) -> int:
    ensure_evaluation_environment(require_isolated=args.load_fixtures)
    cases = load_evaluation_dataset(args.dataset)
    manifest = build_manifest(dataset_name=Path(args.dataset).stem, dataset_version="1", top_k=args.top_k, candidate_limit=20, generation_enabled=not args.retrieval_only)
    use_evaluation_db = args.load_fixtures or os.getenv("MEDILINK_ENVIRONMENT", "").lower() == "evaluation"
    session = (get_evaluation_session_factory() if use_evaluation_db else get_session_factory())()
    try:
        if args.load_fixtures:
            fixture_path = Path(args.fixture_path)
            print(f"Loading controlled evaluation fixtures from {fixture_path}...")
            print(f"Loaded {load_controlled_fixtures(session, fixture_path)} new document(s).")
        if args.retrieval_only:
            retrieval_results = run_retrieval_evaluation(session, cases, k=args.top_k)
            for result in retrieval_results:
                print(
                    f"{result.case_id}: precision@{args.top_k}={result.precision_at_5:.3f} "
                    f"recall@{args.top_k}={result.recall_at_5:.3f} "
                    f"MRR={result.reciprocal_rank:.3f} "
                    f"{'PASS' if result.passed else 'FAIL'}"
                )
            retrieval_summary = summarize_retrieval_results(retrieval_results)
            print(
                f"Baseline: precision@{args.top_k}={retrieval_summary.precision_at_5:.3f} "
                f"recall@{args.top_k}={retrieval_summary.recall_at_5:.3f} "
                f"MRR={retrieval_summary.mean_reciprocal_rank:.3f} "
                f"authorization_leakage={retrieval_summary.authorization_leakage}"
            )
            if args.manifest:
                write_manifest(args.manifest, manifest)
            return 0 if all(result.passed for result in retrieval_results) else 2
        results, summary = await EvaluationRunner(cases, lambda _case: None).run_assistant(HospitalKnowledgeAssistant(session))
    finally:
        session.close()
    release_gate = evaluate_release_gate(results)
    if args.json_report:
        write_json_report(args.json_report, results, summary, args.model)
    if args.markdown_report:
        Path(args.markdown_report).write_text(render_markdown_report(results, summary, args.model), encoding="utf-8")
    if args.manifest:
        write_manifest(args.manifest, manifest)
    print(render_evaluation_report(results, release_gate, args.model, summary))
    return 0 if release_gate.passed and summary.gates_passed else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Medilink AI's controlled reliability evaluation.")
    parser.add_argument("--dataset", default="tests/evaluation/datasets/knowledge_assistant_v1.json")
    parser.add_argument("--model", default="configured-local-model")
    parser.add_argument("--json-report")
    parser.add_argument("--markdown-report")
    parser.add_argument("--load-fixtures", action="store_true", help="Upsert synthetic fixtures into the configured development/evaluation database")
    parser.add_argument("--fixture-path", default="tests/evaluation/fixtures/knowledge_documents.json")
    parser.add_argument("--retrieval-only", action="store_true", help="Evaluate authorized retrieval without calling Ollama")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--manifest", help="Write reproducibility metadata for this benchmark run")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
