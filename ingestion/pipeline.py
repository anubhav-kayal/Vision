"""Command-line entry point for Day 2 document normalization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingestion.chunking import section_aware_chunks
from ingestion.models import ParsedDocument, document_from_manifest
from ingestion.pdf_parser import parse_pdf


def ingest_pdf(
    pdf_path: str | Path,
    manifest_path: str | Path,
    *,
    start_page: int = 1,
    end_page: int | None = None,
) -> ParsedDocument:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    document = document_from_manifest(manifest)
    pages = parse_pdf(pdf_path, start_page=start_page, end_page=end_page)
    chunks = section_aware_chunks(pages, document)
    return ParsedDocument(document=document, source_file=str(pdf_path), pages=pages, chunks=chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize a technical manual PDF")
    parser.add_argument("pdf_path")
    parser.add_argument("manifest_path")
    parser.add_argument("output_path")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--end-page", type=int)
    args = parser.parse_args()
    result = ingest_pdf(
        args.pdf_path,
        args.manifest_path,
        start_page=args.start_page,
        end_page=args.end_page,
    )
    output = Path(args.output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(f"Parsed {len(result.pages)} pages into {len(result.chunks)} chunks: {output}")


if __name__ == "__main__":
    main()
