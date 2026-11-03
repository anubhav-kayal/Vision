"""Provider-independent proposals: no actions or numeric diagnostic probabilities."""

from typing import Protocol
from pydantic import Field

from backend.app.diagnostics.evidence import VisualObservationDraft
from backend.app.diagnostics.models import DiagnosticModel, SupportLevel


class HypothesisDraft(DiagnosticModel):
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    support_level: SupportLevel
    evidence_ids: list[str]
    source_chunk_ids: list[str] = Field(min_length=1)


class AssessmentDraft(DiagnosticModel):
    hypotheses: list[HypothesisDraft]
    evidence_summary: str


class ProviderFailure(RuntimeError):
    pass


class TextModelProvider(Protocol):
    def assess(self, context: str) -> AssessmentDraft: ...


class VisionModelProvider(Protocol):
    def observe(self, evidence_id: str, image: bytes, media_type: str,
                asset_context: str) -> VisualObservationDraft: ...


def validate_proposal(draft, sources, observation_ids):
    allowed = {source.chunk_id for source in sources}
    for hypothesis in draft.hypotheses:
        if not set(hypothesis.source_chunk_ids) <= allowed:
            raise ProviderFailure("UNGROUNDED_SOURCE")
        if not set(hypothesis.evidence_ids) <= set(observation_ids):
            raise ProviderFailure("UNKNOWN_EVIDENCE")
    return draft
