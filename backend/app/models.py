"""Minimal domain contracts for the first industrial AI prototype."""

from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuthorityLevel(StrEnum):
    """Knowledge provenance categories, ordered later by policy rather than by the model."""

    SAFETY_INSTRUCTION = "safety_instruction"
    OEM_SERVICE_BULLETIN = "current_oem_service_bulletin"
    OEM_SERVICE_MANUAL = "current_oem_service_manual"
    GOVERNMENT_TECHNICAL_GUIDE = "government_technical_guide"
    APPROVED_INTERNAL_SOP = "approved_internal_sop"
    VERIFIED_SERVICE_CASE = "verified_historical_service_case"
    UNVERIFIED_TECHNICIAN_NOTE = "unverified_technician_note"
    AI_INFERENCE = "ai_inference"


class DomainModel(BaseModel):
    """Shared strictness and serialization behavior for domain objects."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Asset(DomainModel):
    asset_id: str = Field(min_length=1)
    manufacturer: str = Field(min_length=1)
    family: str | None = None
    equipment_family: str | None = None
    model: str = Field(min_length=1)
    revision: str | None = None
    serial_number: str | None = None
    firmware_version: str | None = None
    site: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_and_normalize_family(self) -> "Asset":
        if not self.family and not self.equipment_family:
            raise ValueError("family or equipment_family is required")
        if not self.family:
            self.family = self.equipment_family
        if not self.equipment_family:
            self.equipment_family = self.family
        return self


class AssetContext(DomainModel):
    """Identity context used to constrain knowledge retrieval and diagnosis."""

    asset_id: str | None = None
    manufacturer: str | None = None
    equipment_family: str | None = None
    model: str | None = None
    revision: str | None = None
    serial_number: str | None = None
    firmware_version: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_asset(cls, asset: Asset) -> "AssetContext":
        return cls(
            asset_id=asset.asset_id,
            manufacturer=asset.manufacturer,
            equipment_family=asset.equipment_family or asset.family,
            model=asset.model,
            revision=asset.revision,
            serial_number=asset.serial_number,
            firmware_version=asset.firmware_version,
            configuration=asset.configuration,
            metadata=asset.metadata,
        )


class KnowledgeDocument(DomainModel):
    document_id: str = Field(min_length=1)
    manufacturer: str = Field(min_length=1)
    equipment_family: str = Field(min_length=1)
    model: str | None = None
    document_type: str = Field(min_length=1)
    revision: str | None = None
    effective_date: date | None = None
    authority_level: AuthorityLevel
    source: str = Field(min_length=1)


class ServiceCase(DomainModel):
    case_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    symptoms: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    expected_next_observation: str | None = None
    root_cause: str | None = None
    resolution: str | None = None
    source_reference: str | None = None


class GroundedSource(DomainModel):
    """A source excerpt that supports a grounded response claim."""

    chunk_id: str | None = None
    document_id: str = Field(min_length=1)
    page: int | str = Field(description="Source page number or a source-defined page label")
    section: str | None = None
    supporting_text: str = Field(min_length=1)


class AnswerStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT_KNOWLEDGE = "INSUFFICIENT_KNOWLEDGE"


class GroundedAnswer(DomainModel):
    """Validated answer boundary; it is not an implementation of generation."""

    status: AnswerStatus
    answer: str = Field(min_length=1)
    sources: list[GroundedSource] = Field(default_factory=list)
    evidence_summary: str | None = None
