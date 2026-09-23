"""Transparent heuristic for selecting the next diagnostic observation."""

from __future__ import annotations

from backend.app.diagnostics.models import (
    EvidenceCandidate,
    EvidenceRequest,
    Observation,
    SafetyStatus,
)


def rank_candidate(
    request: EvidenceRequest,
    *,
    supported_by_documentation: bool,
    discriminates_hypotheses: list[str],
    observations: list[Observation],
    previous_requests: list[EvidenceRequest],
    realistic_for_technician: bool = True,
) -> EvidenceCandidate:
    """Score one candidate using a small auditable heuristic, not Bayesian information gain."""

    already_available = any(
        observation.type.value == request.type.value
        and observation.parameter.casefold() in request.target.casefold()
        for observation in observations
    )
    already_requested = any(
        previous.type is request.type and previous.target.casefold() == request.target.casefold()
        for previous in previous_requests
    )
    score = 0
    score += 3 if supported_by_documentation else -100
    score += 2 * len(discriminates_hypotheses)
    score += 2 if not already_available else -100
    score += 1 if not already_requested else -100
    score += 1 if realistic_for_technician else -2
    score += {
        SafetyStatus.ALLOWED_ADVISORY: 1,
        SafetyStatus.REQUIRES_SUPERVISION: -1,
        SafetyStatus.UNKNOWN: -3,
        SafetyStatus.SAFETY_BLOCK: -100,
    }[request.safety_status]
    reasons = [
        "supported by retrieved documentation" if supported_by_documentation else "not supported by documentation",
        f"tests {len(discriminates_hypotheses)} hypothesis(es)" if discriminates_hypotheses else "does not distinguish hypotheses",
        "not already available" if not already_available else "already available",
        "not previously requested" if not already_requested else "already requested",
        f"safety={request.safety_status.value}",
    ]
    return EvidenceCandidate(
        candidate=request.target,
        request=request,
        supported_by_documentation=supported_by_documentation,
        discriminates_hypotheses=discriminates_hypotheses,
        already_available=already_available,
        already_requested=already_requested,
        realistic_for_technician=realistic_for_technician,
        safety_status=request.safety_status,
        score=score,
        selection_reason="; ".join(reasons),
    )


def select_next_evidence(candidates: list[EvidenceCandidate]) -> EvidenceCandidate | None:
    """Return the highest-scoring actionable candidate, or none if all are unsafe/stale."""

    actionable = [
        candidate
        for candidate in candidates
        if candidate.supported_by_documentation
        and not candidate.already_available
        and not candidate.already_requested
        and candidate.safety_status is not SafetyStatus.SAFETY_BLOCK
        and candidate.safety_status is not SafetyStatus.UNKNOWN
    ]
    actionable.sort(key=lambda candidate: (-candidate.score, candidate.candidate))
    return actionable[0] if actionable else None
