"""Synchronous pilot ingestion with explicit processing and rejection records."""

from backend.app.catalog import ProcessingStatus
from backend.app.catalog_service import CatalogService
from ingestion.chunking import section_aware_chunks
from ingestion.models import ParsedDocument
from ingestion.pdf_parser import parse_pdf


class IngestionService:
    def __init__(self, catalog: CatalogService, parser=parse_pdf):
        self.catalog, self.parser = catalog, parser

    def ingest(self, revision_id, path):
        record = self.catalog.require("documents", revision_id)
        if record.status is not ProcessingStatus.UPLOADED:
            raise ValueError("only newly uploaded documents can be ingested")
        record.status = ProcessingStatus.PROCESSING
        self.catalog.repository.put("documents", record.id, record)
        try:
            pages = self.parser(path)
            chunks = section_aware_chunks(pages, record.document)
            if not pages or not chunks:
                raise ValueError("manual contains no extractable text")
            record.parsed = ParsedDocument(
                document=record.document, source_file=str(path), pages=pages, chunks=chunks,
            )
            record.status = ProcessingStatus.READY
        except (ValueError, OSError, RuntimeError):
            record.status = ProcessingStatus.REJECTED
            record.failure_reason = "MANUAL_PARSE_FAILED"
        self.catalog.repository.put("documents", record.id, record)
        return record
