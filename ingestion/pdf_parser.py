"""PDF text extraction with page and coarse section preservation."""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from ingestion.models import ParsedPage

_PRINTED_PAGE_RE = re.compile(r"\b(\d+[-–]\d+|\d+|[ivxlcdm]+)\s*$", re.IGNORECASE)
_PAGE_HEADER_RE = re.compile(r"^(TM|TB|FM|TECHNICAL MANUAL)\b", re.IGNORECASE)


def _clean_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for line in raw_text.splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return lines


def _is_heading(line: str) -> bool:
    """Recognize conservative all-caps headings without treating body lines as headings."""

    letters = re.sub(r"[^A-Za-z]", "", line)
    if (
        not 3 <= len(letters) <= 80
        or _PAGE_HEADER_RE.match(line)
        or "..." in line
        or line.startswith("IMPROVING COMPRESSED AIR SYSTEM PERFORMANCE:")
    ):
        return False
    return letters.upper() == letters and len(line.split()) <= 12


def _extract_printed_label(lines: list[str]) -> str | None:
    for line in lines:
        header_match = re.search(r"\|\s*(\d+)\s*$", line)
        if header_match and line.startswith("IMPROVING COMPRESSED AIR SYSTEM PERFORMANCE:"):
            return header_match.group(1)
    for line in reversed(lines[-5:]):
        match = _PRINTED_PAGE_RE.search(line)
        if match:
            return match.group(1)
    return None


def parse_pdf(path: str | Path, *, start_page: int = 1, end_page: int | None = None) -> list[ParsedPage]:
    """Extract selected 1-indexed PDF pages while retaining page boundaries."""

    pdf_path = Path(path)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    if start_page < 1:
        raise ValueError("start_page must be 1 or greater")

    document = pymupdf.open(pdf_path)
    final_page = min(end_page or document.page_count, document.page_count)
    if start_page > final_page:
        raise ValueError("start_page must not exceed end_page or the document page count")

    pages: list[ParsedPage] = []
    for page_number in range(start_page, final_page + 1):
        lines = _clean_lines(document[page_number - 1].get_text("text"))
        if not lines:
            continue
        printed_page_label = _extract_printed_label(lines)
        lines = [
            line
            for line in lines
            if not line.startswith("IMPROVING COMPRESSED AIR SYSTEM PERFORMANCE:")
        ]
        if not lines:
            continue
        sections = [line for line in lines if _is_heading(line)]
        pages.append(
            ParsedPage(
                pdf_page_number=page_number,
                printed_page_label=printed_page_label,
                text="\n".join(lines),
                sections=sections,
            )
        )
    document.close()
    return pages
