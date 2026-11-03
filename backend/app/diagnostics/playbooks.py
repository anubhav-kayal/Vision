"""Approved source-bound playbooks. No OEM facts are bundled as approved guidance."""

import json
import re
from pydantic import Field, ValidationError

from backend.app.diagnostics.models import (
    DiagnosticAssessment, DiagnosticModel, DiagnosticRetrievalLog, DiagnosticStatus,
    EvidenceRequest, Hypothesis, SafetyStatus, SupportLevel,
)
from backend.app.models import GroundedSource
from backend.app.providers import AssessmentDraft, ProviderFailure, validate_proposal

PILOT_FAULTS = {
    "fails_to_start": ["fails to start", "will not start", "won't start"],
    "high_coolant_temperature": ["high coolant temperature", "overheating"],
    "low_oil_pressure": ["low oil pressure"],
    "low_output_voltage": ["low output voltage", "low voltage"],
    "abnormal_vibration": ["excessive vibration", "abnormal noise"],
}


class Playbook(DiagnosticModel):
    id: str = Field(min_length=1)
    fault: str = Field(min_length=1)
    manufacturer: str = Field(min_length=1)
    model: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    approved_by: str = Field(min_length=1)
    approval_reference: str = Field(min_length=1)
    source: GroundedSource
    hypothesis: str = Field(min_length=1)
    evidence_request: EvidenceRequest


class PlaybookEngine:
    def __init__(self, index, playbooks=(), provider=None):
        self.index, self.playbooks, self.provider = index, list(playbooks), provider

    def assess(self, asset, reported_problem, *, symptoms=None, observations=None,
               previous_requests=None):
        observations, previous_requests = observations or [], previous_requests or []
        sources = self.index.retrieve(reported_problem, top_k=8, asset_context=asset)
        log = DiagnosticRetrievalLog(
            query=reported_problem, asset_filters=asset.model_dump(exclude_none=True),
            retrieved_chunk_ids=[s.chunk_id for s in sources],
            retrieved_scores={s.chunk_id: s.score for s in sources},
        )
        def stop(status, reason):
            return DiagnosticAssessment(status=status, summary=reason, limitations=[reason], retrieval=log)
        if not sources:
            return stop(DiagnosticStatus.INSUFFICIENT_KNOWLEDGE, "NO_APPLICABLE_EVIDENCE")
        problem = " ".join([reported_problem, *(s.description for s in symptoms or [])]).casefold()
        if re.search(r"\b(bypass|rewire|disable interlock|open live|replace avr)\b", problem):
            return stop(DiagnosticStatus.SAFETY_BLOCK, "RESTRICTED_WORK_REQUESTED")
        faults = [key for key, terms in PILOT_FAULTS.items()
                  if any(re.search(r"\b" + re.escape(term) + r"\b", problem) for term in terms)]
        if len(faults) != 1:
            return stop(DiagnosticStatus.ESCALATE, "UNKNOWN_OR_AMBIGUOUS_FAULT")
        eligible = [p for p in self.playbooks if p.fault == faults[0] and all(
            getattr(p, k).casefold() == (getattr(asset, k) or "").casefold()
            for k in ("manufacturer", "model", "revision"))]
        if len(eligible) != 1:
            return stop(DiagnosticStatus.ESCALATE, "NO_UNIQUE_APPROVED_PLAYBOOK")
        playbook = eligible[0]
        refs = [playbook.source, *playbook.evidence_request.source_references]
        for ref in refs:
            if not any(ref.chunk_id == s.chunk_id and ref.document_id == s.document_id
                       and str(ref.page) in {str(s.page), str(s.printed_page)}
                       and (not ref.section or ref.section == s.section)
                       and ref.supporting_text in s.text for s in sources):
                return stop(DiagnosticStatus.INSUFFICIENT_KNOWLEDGE, "PLAYBOOK_SOURCE_NOT_RETRIEVED")
        if not playbook.evidence_request.source_references:
            return stop(DiagnosticStatus.INSUFFICIENT_KNOWLEDGE, "REQUEST_SOURCE_MISSING")
        if self.provider:
            try:
                draft = self.provider.assess(json.dumps(dict(
                    problem=problem, observations=[o.model_dump(mode="json") for o in observations],
                    sources=[s.model_dump(mode="json") for s in sources],
                    allowed_hypotheses=[dict(label=playbook.id, description=playbook.hypothesis)],
                )))
                draft = AssessmentDraft.model_validate(draft)
                validate_proposal(draft, sources, [o.observation_id for o in observations])
                if not draft.hypotheses:
                    return stop(DiagnosticStatus.INSUFFICIENT_KNOWLEDGE, "MODEL_FOUND_NO_SUPPORT")
                if any(h.label != playbook.id for h in draft.hypotheses):
                    raise ProviderFailure("UNAPPROVED_HYPOTHESIS")
            except (ProviderFailure, ValidationError, TypeError):
                return stop(DiagnosticStatus.ESCALATE, "MODEL_UNAVAILABLE_OR_UNGROUNDED")
        request = playbook.evidence_request.model_copy(deep=True)
        if request.safety_status is SafetyStatus.SAFETY_BLOCK:
            return stop(DiagnosticStatus.SAFETY_BLOCK, "REQUEST_BLOCKED")
        if request.safety_status is not SafetyStatus.ALLOWED_ADVISORY:
            return stop(DiagnosticStatus.ESCALATE, "QUALIFIED_REVIEW_REQUIRED")
        hypothesis = Hypothesis(
            hypothesis_id=playbook.id, description=playbook.hypothesis,
            support_level=SupportLevel.WEAKLY_SUPPORTED, source_references=[playbook.source],
        )
        request.related_hypotheses = [hypothesis.hypothesis_id]
        available = any(o.parameter.casefold() == request.target.casefold() for o in observations)
        repeated = any(r.type == request.type and r.target == request.target for r in previous_requests)
        return DiagnosticAssessment(
            status=DiagnosticStatus.ESCALATE if available or repeated else DiagnosticStatus.NEED_EVIDENCE,
            summary="REVIEW_COLLECTED_EVIDENCE" if available or repeated else "COLLECT_DOCUMENTED_EVIDENCE",
            hypotheses=[hypothesis], next_evidence_request=None if available or repeated else request,
            sources=refs, retrieval=log,
            limitations=["Advisory only. This playbook does not establish a verified diagnosis or authorize repair."],
        )
