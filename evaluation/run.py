"""Reproducible deterministic evaluation runner for the Week 1 baseline."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.models import AnswerStatus
from evaluation.case_models import EvaluationCase, load_cases
from ingestion.chunking import fixed_size_chunks
from ingestion.models import ParsedDocument
from ingestion.retrieval import TfidfIndex, tokenize


def _retrieved_pages(results: list[Any]) -> set[str]:
    return {str(result.printed_page) for result in results if result.printed_page is not None}


def _fact_coverage(case: EvaluationCase, results: list[Any]) -> float | None:
    if not case.expected_key_facts:
        return None
    evidence_tokens = set(tokenize(" ".join(result.text for result in results)))
    fact_scores = []
    for fact in case.expected_key_facts:
        tokens = set(tokenize(fact))
        fact_scores.append(len(tokens & evidence_tokens) / len(tokens) if tokens else 0.0)
    return round(sum(fact_scores) / len(fact_scores), 4)


def _evaluate_case(case: EvaluationCase, index: TfidfIndex, top_k: int) -> dict[str, Any]:
    results = index.retrieve(case.query, top_k=top_k)
    pages = _retrieved_pages(results)
    expected_pages = set(case.expected_printed_pages)
    has_page_hit = bool(expected_pages & pages) if expected_pages else not results
    source_hit = (
        case.expected_source_document is not None
        and any(result.document_id == case.expected_source_document for result in results)
        and bool(expected_pages & pages)
    )
    correct_refusal = (
        case.expected_status is AnswerStatus.INSUFFICIENT_KNOWLEDGE and not results
    )
    if (
        case.expected_status is AnswerStatus.SUPPORTED and not has_page_hit
    ) or (
        case.expected_status is AnswerStatus.INSUFFICIENT_KNOWLEDGE and results
    ):
        failure_category = "RETRIEVAL_FAILURE"
    elif case.expected_status is AnswerStatus.SUPPORTED and _fact_coverage(case, results) == 0:
        failure_category = "CONTEXT_FAILURE"
    else:
        failure_category = None
    return {
        "case_id": case.case_id,
        "query": case.query,
        "expected_status": case.expected_status.value,
        "retrieved_pages": sorted(pages),
        "top_results": [result.model_dump() for result in results],
        "retrieval_hit": has_page_hit,
        "correct_source": source_hit,
        "expected_fact_coverage": _fact_coverage(case, results),
        "correct_refusal": correct_refusal,
        "failure_category": failure_category,
    }


def evaluate_strategy(
    cases: list[EvaluationCase], index: TfidfIndex, *, top_k: int
) -> dict[str, Any]:
    case_results = [_evaluate_case(case, index, top_k) for case in cases]
    supported = [case for case in case_results if case["expected_status"] == AnswerStatus.SUPPORTED]
    refusal_cases = [
        case for case in case_results if case["expected_status"] == AnswerStatus.INSUFFICIENT_KNOWLEDGE
    ]
    fact_scores = [
        case["expected_fact_coverage"]
        for case in supported
        if case["expected_fact_coverage"] is not None
    ]
    return {
        "strategy": index.strategy,
        "metrics": {
            "cases": len(case_results),
            "retrieval_hit_rate": round(
                sum(case["retrieval_hit"] for case in supported) / len(supported), 4
            ),
            "correct_source_rate": round(
                sum(case["correct_source"] for case in supported) / len(supported), 4
            ),
            "expected_fact_coverage": round(sum(fact_scores) / len(fact_scores), 4)
            if fact_scores
            else None,
            "correct_refusal_rate": round(
                sum(case["correct_refusal"] for case in refusal_cases) / len(refusal_cases), 4
            )
            if refusal_cases
            else None,
            "unsupported_claim_rate": None,
        },
        "metric_notes": {
            "unsupported_claim_rate": "Not measured: no live/generated model output was evaluated in this baseline.",
            "retrieval_hit_rate": "Expected printed-page hit among supported cases at top-k.",
            "correct_source_rate": "Expected document and expected page both present among retrieved results.",
        },
        "failed_cases": [
            {
                "case_id": case["case_id"],
                "category": case["failure_category"],
            }
            for case in case_results
            if case["failure_category"]
        ],
        "cases": case_results,
    }


def run_evaluation(parsed_path: str, cases_path: str, *, top_k: int) -> dict[str, Any]:
    parsed = ParsedDocument.model_validate_json(Path(parsed_path).read_text(encoding="utf-8"))
    cases = load_cases(cases_path)
    fixed_chunks = fixed_size_chunks(parsed.pages, parsed.document, max_chars=1200)
    indexes = {
        "fixed_size": TfidfIndex(fixed_chunks),
        "section_aware": TfidfIndex(parsed.chunks),
    }
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "model": "not_run",
        "embedding_model": "tfidf-local",
        "retrieval_configuration": {
            "top_k": top_k,
            "fixed_size_chars": 1200,
            "section_aware_chars": 1800,
        },
        "prompt_version": "not_applicable",
        "source_document": parsed.document.model_dump(mode="json"),
        "strategies": {
            name: evaluate_strategy(cases, index, top_k=top_k)
            for name, index in indexes.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Week 1 deterministic evaluation")
    parser.add_argument("--parsed", default="sample_data/parsed/doe-ee-1340.full.json")
    parser.add_argument("--cases", default="evaluation/cases/week1_v0.json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", default="evaluation/results/week1_baseline.json")
    args = parser.parse_args()
    report = run_evaluation(args.parsed, args.cases, top_k=args.top_k)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Industrial AI Evaluation")
    print(f"Cases: {len(load_cases(args.cases))}")
    for strategy, result in report["strategies"].items():
        metrics = result["metrics"]
        print(f"\nStrategy: {strategy}")
        print(f"Retrieval Hit Rate: {metrics['retrieval_hit_rate']:.1%}")
        print(f"Correct Source: {metrics['correct_source_rate']:.1%}")
        print(f"Expected Fact Coverage: {metrics['expected_fact_coverage']:.1%}")
        print(f"Correct Refusal: {metrics['correct_refusal_rate']:.1%}")
        print("Unsupported Claims: NOT MEASURED")
        print("Failed Cases:", [case["case_id"] for case in result["failed_cases"]])
    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
