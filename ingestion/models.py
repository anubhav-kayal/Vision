"""Normalized document representations used by the ingestion pipeline."""

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models import KnowledgeDocument


class ParsedPage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    pdf_page_number: int = Field(ge=1)
    printed_page_label: str | None = None
    text: str = Field(min_length=1)
    sections: list[str] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    chunk_id: str = Field(min_length=1)
    document: KnowledgeDocument
    pdf_page_number: int = Field(ge=1)
    printed_page_label: str | None = None
    section: str | None = None
    text: str = Field(min_length=1)
    chunking_strategy: str = Field(min_length=1)


class ParsedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: KnowledgeDocument
    source_file: str = Field(min_length=1)
    pages: list[ParsedPage] = Field(default_factory=list)
    chunks: list[DocumentChunk] = Field(default_factory=list)


def document_from_manifest(manifest: dict) -> KnowledgeDocument:
    """Validate and convert the human-maintained document manifest."""

    return KnowledgeDocument.model_validate(manifest)


__all__ = ["DocumentChunk", "ParsedDocument", "ParsedPage", "document_from_manifest"]
