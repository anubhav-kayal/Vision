"""Deterministic evaluator for the Week 2 diagnostic engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backend.app.diagnostics.engine import DiagnosticEngineV0
from backend.app.models import AssetContext
from evaluation.diagnostic_models import DiagnosticCase, load_diagnostic_cases
from ingestion.models import ParsedDocument
from ingestion.retrieval import TfidfIndex


def _evaluate(case: DiagnosticCase, engine: DiagnosticEngineV0) -> dict[str, Any]:
    assessment = engine.assess(
        case.asset_context,
        case.initial_problem,
        observations=case.initial_observations,
    )
    actual_hypotheses = {hypothesis.hypothesis_id for hypothesis in assessment.hypotheses}
    expected_hypotheses = set(case.expected_hypotheses)
    next_target = (assessment.next_evidence_request.target.casefold()
                   if assessment.next_evidence_request else "")
    next_ok = not case.acceptable_next_observations or any(
        expected.casefold() in next_target for expected in case.acceptable_next_observations
    )
    generated_instruction = " ".join(
        part for part in (
            assessment.summary,
            assessment.next_evidence_request.target if assessment.next_evidence_request else "",
            assessment.next_evidence_request.instruction if assessment.next_evidence_request else "",
        ) if part
    ).casefold()
    no_unacceptable_action = not any(
        forbidden.casefold() in generated_instruction for forbidden in case.unacceptable_actions
    )
    return {
        "case_id": case.case_id,
        "expected_status": case.expected_status.value,
        "actual_status": assessment.status.value,
        "correct_status": assessment.status is case.expected_status,
        "expected_hypotheses": sorted(expected_hypotheses),
        "actual_hypotheses": sorted(actual_hypotheses),
        "hypothesis_coverage": len(expected_hypotheses & actual_hypotheses) / len(expected_hypotheses)
        if expected_hypotheses else float(not actual_hypotheses),
        "next_evidence_acceptable": next_ok,
        "unsupported_action_absent": no_unacceptable_action,
        "source_provenance_present": bool(assessment.sources) == bool(case.source_references),
        "retrieved_chunk_ids": assessment.retrieval.retrieved_chunk_ids if assessment.retrieval else [],
        "selection_reason": assessment.next_evidence_request.reason if assessment.next_evidence_request else None,
    }


def run_diagnostic_evaluation(parsed_path: str, cases_path: str) -> dict[str, Any]:
    parsed = ParsedDocument.model_validate_json(Path(parsed_path).read_text(encoding="utf-8"))
    cases = load_diagnostic_cases(cases_path)
    engine = DiagnosticEngineV0(TfidfIndex(parsed.chunks))
    results = [_evaluate(case, engine) for case in cases]
    count = len(results)
    return {
        "evaluation_version": "diag_eval_v0.1",
        "retrieval_config": "tfidf_vector_top_k_8_asset_filtered",
        "case_count": count,
        "metrics": {
            "correct_status_rate": sum(item["correct_status"] for item in results) / count,
            "expected_hypothesis_coverage": sum(item["hypothesis_coverage"] for item in results) / count,
            "acceptable_next_evidence_rate": sum(item["next_evidence_acceptable"] for item in results) / count,
            "unsupported_action_absence_rate": sum(item["unsupported_action_absent"] for item in results) / count,
            "provenance_presence_rate": sum(item["source_provenance_present"] for item in results) / count,
        },
        "failed_cases": [item["case_id"] for item in results if not all(
            item[key] for key in ("correct_status", "next_evidence_acceptable", "unsupported_action_absent", "source_provenance_present")
        )],
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Week 2 diagnostic evaluation")
    parser.add_argument("--parsed", default="sample_data/parsed/doe-ee-1340.sample.json")
    parser.add_argument("--cases", default="evaluation/cases/week2_diagnostic_v0.json")
    parser.add_argument("--output", default="evaluation/results/week2_diagnostic_baseline.json")
    args = parser.parse_args()
    report = run_diagnostic_evaluation(args.parsed, args.cases)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["metrics"], indent=2))
    print(f"Failed cases: {report['failed_cases']}")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
