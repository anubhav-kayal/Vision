"""Minimal, validated structures for an evidence-first diagnostic session."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.models import Asset, GroundedSource


class DiagnosticModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ConfidenceLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ObservationType(StrEnum):
    MEASUREMENT = "measurement"
    VISUAL = "visual"
    AUDIO = "audio"
    FAULT_CODE = "fault_code"
    TECHNICIAN_REPORT = "technician_report"
    SENSOR = "sensor"
    DOCUMENTED_HISTORY = "documented_history"


class VerificationStatus(StrEnum):
    TECHNICIAN_REPORTED = "technician_reported"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class HypothesisStatus(StrEnum):
    ACTIVE = "active"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    REJECTED = "rejected"


class SupportLevel(StrEnum):
    WEAKLY_SUPPORTED = "WEAKLY_SUPPORTED"
    SUPPORTED = "SUPPORTED"
    STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"
    UNKNOWN = "UNKNOWN"


class EvidenceRequestType(StrEnum):
    MEASUREMENT = "measurement"
    VISUAL = "visual"
    AUDIO = "audio"
    FAULT_CODE = "fault_code"
    TECHNICIAN_REPORT = "technician_report"
    DOCUMENTED_HISTORY = "documented_history"


class SafetyStatus(StrEnum):
    ALLOWED_ADVISORY = "ALLOWED_ADVISORY"
    REQUIRES_SUPERVISION = "REQUIRES_SUPERVISION"
    SAFETY_BLOCK = "SAFETY_BLOCK"
    UNKNOWN = "UNKNOWN"


class DiagnosticStatus(StrEnum):
    NEED_EVIDENCE = "NEED_EVIDENCE"
    DIAGNOSIS_SUPPORTED = "DIAGNOSIS_SUPPORTED"
    INSUFFICIENT_KNOWLEDGE = "INSUFFICIENT_KNOWLEDGE"
    SAFETY_BLOCK = "SAFETY_BLOCK"
    ESCALATE = "ESCALATE"


class DiagnosticRetrievalLog(DiagnosticModel):
    query: str = Field(min_length=1)
    asset_filters: dict[str, Any] = Field(default_factory=dict)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    retrieved_scores: dict[str, float] = Field(default_factory=dict)


class DiagnosticAssessment(DiagnosticModel):
    status: DiagnosticStatus
    summary: str = Field(min_length=1)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    next_evidence_request: EvidenceRequest | None = None
    sources: list[GroundedSource] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    retrieval: DiagnosticRetrievalLog | None = None
    evidence_candidates: list["EvidenceCandidate"] = Field(default_factory=list)


def utc_now() -> datetime:
    return datetime.now(UTC)


class Symptom(DiagnosticModel):
    """A technician-reported problem statement, not verified evidence."""

    symptom_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    reported_by: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=utc_now)
    confidence: ConfidenceLevel | None = None


class Observation(DiagnosticModel):
    """An observation or measurement captured during an investigation."""

    observation_id: str = Field(min_length=1)
    type: ObservationType
    parameter: str = Field(min_length=1)
    value: Any
    unit: str | None = None
    source: str = Field(min_length=1)
    verification_status: VerificationStatus = VerificationStatus.TECHNICIAN_REPORTED
    timestamp: datetime = Field(default_factory=utc_now)
    supersedes_observation_id: str | None = None
    superseded_by_observation_id: str | None = None
    correction_reason: str | None = None

    @model_validator(mode="after")
    def validate_value_for_type(self) -> "Observation":
        if self.type is ObservationType.MEASUREMENT and (
            not isinstance(self.value, (int, float)) or isinstance(self.value, bool)
        ):
            raise ValueError("measurement observations require a numeric value")
        if self.type is ObservationType.FAULT_CODE and not isinstance(self.value, str):
            raise ValueError("fault_code observations require a string value")
        if self.type in {ObservationType.VISUAL, ObservationType.AUDIO} and not isinstance(
            self.value, str
        ):
            raise ValueError("visual and audio observations require a text description or reference")
        if self.type is ObservationType.MEASUREMENT and not self.unit:
            raise ValueError("measurement observations require a unit")
        if self.supersedes_observation_id and not self.correction_reason:
            raise ValueError("correction_reason is required when superseding an observation")
        return self


class Hypothesis(DiagnosticModel):
    hypothesis_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    support_level: SupportLevel = SupportLevel.UNKNOWN
    source_references: list[GroundedSource] = Field(default_factory=list)


class EvidenceRequest(DiagnosticModel):
    request_id: str = Field(min_length=1)
    type: EvidenceRequestType
    target: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    related_hypotheses: list[str] = Field(default_factory=list)
    source_references: list[GroundedSource] = Field(default_factory=list)
    safety_status: SafetyStatus = SafetyStatus.UNKNOWN


class EvidenceCandidate(DiagnosticModel):
    """Inspectable candidate used by the V0 next-evidence selector."""

    candidate: str = Field(min_length=1)
    request: EvidenceRequest
    supported_by_documentation: bool
    discriminates_hypotheses: list[str] = Field(default_factory=list)
    already_available: bool = False
    already_requested: bool = False
    realistic_for_technician: bool = True
    safety_status: SafetyStatus
    score: int
    selection_reason: str = Field(min_length=1)


class DiagnosticSession(DiagnosticModel):
    """State of one evidence-first diagnostic investigation."""

    session_id: str = Field(min_length=1)
    asset: Asset
    reported_problem: str = Field(min_length=1)
    symptoms: list[Symptom] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    evidence_requests: list[EvidenceRequest] = Field(default_factory=list)
    status: DiagnosticStatus = DiagnosticStatus.NEED_EVIDENCE
    sources: list[GroundedSource] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_references(self) -> "DiagnosticSession":
        observation_ids = {observation.observation_id for observation in self.observations}
        hypothesis_ids = {hypothesis.hypothesis_id for hypothesis in self.hypotheses}

        if len(observation_ids) != len(self.observations):
            raise ValueError("observation_id values must be unique within a session")
        if len(hypothesis_ids) != len(self.hypotheses):
            raise ValueError("hypothesis_id values must be unique within a session")
        for hypothesis in self.hypotheses:
            referenced = set(hypothesis.supporting_evidence + hypothesis.contradicting_evidence)
            unknown = referenced - observation_ids
            if unknown:
                raise ValueError(
                    f"hypothesis {hypothesis.hypothesis_id} references unknown observations: {sorted(unknown)}"
                )
        for observation in self.observations:
            if observation.supersedes_observation_id:
                if observation.supersedes_observation_id not in observation_ids:
                    raise ValueError(
                        f"observation {observation.observation_id} supersedes an unknown observation"
                    )
                target = next(
                    item
                    for item in self.observations
                    if item.observation_id == observation.supersedes_observation_id
                )
                if target.superseded_by_observation_id not in {
                    None,
                    observation.observation_id,
                }:
                    raise ValueError("an observation cannot be superseded more than once")
                target.superseded_by_observation_id = observation.observation_id
        for request in self.evidence_requests:
            unknown = set(request.related_hypotheses) - hypothesis_ids
            if unknown:
                raise ValueError(
                    f"evidence request {request.request_id} references unknown hypotheses: {sorted(unknown)}"
                )
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be earlier than created_at")
        return self

    def active_observations(self) -> list[Observation]:
        """Return observations not superseded by a later correction."""

        return [
            observation
            for observation in self.observations
            if observation.superseded_by_observation_id is None
        ]

    def add_observation(self, observation: Observation) -> "DiagnosticSession":
        """Append evidence, preserving any observation that the new one corrects."""

        updated = self.model_copy(deep=True)
        if observation.supersedes_observation_id:
            target = next(
                (
                    item
                    for item in updated.observations
                    if item.observation_id == observation.supersedes_observation_id
                ),
                None,
            )
            if target is None:
                raise ValueError("correction target is not present in this session")
            target.superseded_by_observation_id = observation.observation_id
        updated.observations.append(observation)
        updated.updated_at = utc_now()
        return DiagnosticSession.model_validate(updated)

    def record_evidence_request(self, request: EvidenceRequest) -> "DiagnosticSession":
        """Append a request once; identical target/type requests are not duplicated."""

        if any(
            existing.type is request.type and existing.target.casefold() == request.target.casefold()
            for existing in self.evidence_requests
        ):
            return self
        updated = self.model_copy(deep=True)
        updated.evidence_requests.append(request)
        updated.updated_at = utc_now()
        return DiagnosticSession.model_validate(updated)
