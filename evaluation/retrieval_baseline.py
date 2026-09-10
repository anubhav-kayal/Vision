"""Run a small retrieval inspection against fixed and section-aware corpora."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingestion.chunking import fixed_size_chunks
from ingestion.models import ParsedDocument
from ingestion.retrieval import TfidfIndex


def load_cases(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_case(index: TfidfIndex, case: dict, *, top_k: int) -> dict:
    results = index.retrieve(case["query"], top_k=top_k)
    expected_pages = set(case["expected_printed_pages"])
    retrieved_pages = {result.printed_page for result in results}
    return {
        "case_id": case["case_id"],
        "query": case["query"],
        "top_results": [result.model_dump() for result in results],
        "page_hit": bool(expected_pages & retrieved_pages) if expected_pages else not results,
        "strategy": index.strategy,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Day 3 retrieval results")
    parser.add_argument("parsed_document")
    parser.add_argument("cases")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fixed-size", type=int, default=1200)
    parser.add_argument("--output")
    args = parser.parse_args()

    parsed = ParsedDocument.model_validate_json(Path(args.parsed_document).read_text())
    fixed_chunks = fixed_size_chunks(parsed.pages, parsed.document, max_chars=args.fixed_size)
    indexes = {
        "fixed_size": TfidfIndex(fixed_chunks),
        "section_aware": TfidfIndex(parsed.chunks),
    }
    cases = load_cases(args.cases)
    report = {
        strategy: [evaluate_case(index, case, top_k=args.top_k) for case in cases]
        for strategy, index in indexes.items()
    }
    for strategy, results in report.items():
        hits = sum(result["page_hit"] for result in results)
        print(f"{strategy}: {hits}/{len(results)} page-hit cases")
        for result in results:
            pages = [item["printed_page"] for item in result["top_results"][:3]]
            print(f"  {result['case_id']}: {pages}")
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
