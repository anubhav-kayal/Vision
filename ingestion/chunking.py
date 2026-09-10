"""Simple, inspectable chunking strategies for parsed pages."""

from __future__ import annotations

from ingestion.models import DocumentChunk, ParsedPage


def _make_chunk(
    *, document, page: ParsedPage, text: str, section: str | None, index: int, strategy: str
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"{document.document_id}-p{page.pdf_page_number}-c{index}",
        document=document,
        pdf_page_number=page.pdf_page_number,
        printed_page_label=page.printed_page_label,
        section=section,
        text=text.strip(),
        chunking_strategy=strategy,
    )


def fixed_size_chunks(
    pages: list[ParsedPage], document, *, max_chars: int = 1200, overlap: int = 150
) -> list[DocumentChunk]:
    """Create deterministic page-preserving character windows for a baseline."""

    if max_chars <= 0 or overlap < 0 or overlap >= max_chars:
        raise ValueError("require max_chars > overlap >= 0")
    chunks: list[DocumentChunk] = []
    for page in pages:
        start = 0
        index = 0
        while start < len(page.text):
            end = min(start + max_chars, len(page.text))
            chunks.append(
                _make_chunk(
                    document=document,
                    page=page,
                    text=page.text[start:end],
                    section=None,
                    index=index,
                    strategy="fixed_size",
                )
            )
            index += 1
            if end == len(page.text):
                break
            start = end - overlap
    return chunks


def section_aware_chunks(pages: list[ParsedPage], document, *, max_chars: int = 1800) -> list[DocumentChunk]:
    """Split pages at detected headings, then bound unusually large sections."""

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")
    chunks: list[DocumentChunk] = []
    for page in pages:
        current_section: str | None = None
        current_lines: list[str] = []
        page_index = 0

        def flush(page: ParsedPage, section: str | None) -> None:
            nonlocal page_index, current_lines
            text = " ".join(current_lines).strip()
            if not text:
                current_lines = []
                return
            for offset in range(0, len(text), max_chars):
                chunks.append(
                    _make_chunk(
                        document=document,
                        page=page,
                        text=text[offset : offset + max_chars],
                        section=section,
                        index=page_index,
                        strategy="section_aware",
                    )
                )
                page_index += 1
            current_lines = []

        for line in page.text.splitlines():
            if line in page.sections:
                flush(page, current_section)
                current_section = line
            else:
                current_lines.append(line)
        flush(page, current_section)
    return chunks
