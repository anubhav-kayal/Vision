"""Image provenance and unverified vision output contracts; no upload or inference yet."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator

from backend.app.diagnostics.models import (
    ConfidenceLevel, DiagnosticModel, VerificationStatus, utc_now,
)


class ObservationSource(StrEnum):
    TECHNICIAN = "technician"
    MODEL = "model"
    SENSOR = "sensor"
    DOCUMENT = "document"


class ImageEvidence(DiagnosticModel):
    """Metadata only. The future upload service must validate the actual bytes."""

    evidence_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    storage_key: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    media_type: Literal["image/jpeg", "image/png", "image/webp"]
    size_bytes: int = Field(gt=0, strict=True)
    uploaded_by: str = Field(min_length=1)
    uploaded_at: datetime = Field(default_factory=utc_now)


class VisualObservationDraft(DiagnosticModel):
    """Model proposals cannot claim verification or bypass human confirmation."""

    evidence_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_kind: Literal[ObservationSource.MODEL] = ObservationSource.MODEL
    verification_status: Literal[VerificationStatus.UNVERIFIED] = VerificationStatus.UNVERIFIED
    requires_confirmation: Literal[True] = True
    confidence: ConfidenceLevel | None = None

    @field_validator("requires_confirmation", mode="before")
    @classmethod
    def require_explicit_confirmation_flag(cls, value):
        if value is not True:
            raise ValueError("model observations must require confirmation")
        return value
