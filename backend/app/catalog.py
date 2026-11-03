"""Asset and knowledge records shared by memory and SQL repositories."""

from enum import StrEnum
from typing import Protocol

from pydantic import Field, model_validator

from backend.app.models import Asset, DomainModel, KnowledgeDocument
from ingestion.models import ParsedDocument


class Organization(DomainModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)


class Site(Organization):
    organization_id: str = Field(min_length=1)


class RegisteredAsset(DomainModel):
    site_id: str = Field(min_length=1)
    asset: Asset


class ProcessingStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class DocumentRecord(DomainModel):
    id: str = Field(min_length=1, description="Immutable document revision identifier")
    site_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    document: KnowledgeDocument
    status: ProcessingStatus = ProcessingStatus.UPLOADED
    failure_reason: str | None = None
    parsed: ParsedDocument | None = None

    @model_validator(mode="after")
    def validate_ready_content(self):
        if self.status is ProcessingStatus.READY:
            if not self.parsed or not self.parsed.pages or not self.parsed.chunks:
                raise ValueError("ready documents require parsed pages and chunks")
            if self.parsed.document != self.document or any(
                chunk.document != self.document for chunk in self.parsed.chunks
            ):
                raise ValueError("parsed content must preserve document identity")
        return self


class CatalogRepository(Protocol):
    def put(self, kind: str, identifier: str, value: DomainModel) -> None: ...
    def get(self, kind: str, identifier: str) -> DomainModel | None: ...
    def list(self, kind: str) -> list[DomainModel]: ...


MODELS = {"organizations": Organization, "sites": Site,
          "assets": RegisteredAsset, "documents": DocumentRecord}


class MemoryCatalog:
    def __init__(self):
        self.records = {}

    def put(self, kind, identifier, value):
        self.records[kind, identifier] = MODELS[kind].model_validate(value).model_copy(deep=True)

    def get(self, kind, identifier):
        value = self.records.get((kind, identifier))
        return value.model_copy(deep=True) if value else None

    def list(self, kind):
        return [v.model_copy(deep=True) for (k, _), v in self.records.items() if k == kind]
