from backend.app.diagnostics.evidence_selection import rank_candidate, select_next_evidence
from backend.app.diagnostics.models import EvidenceRequest, EvidenceRequestType, SafetyStatus


def make_request(target: str, safety: SafetyStatus = SafetyStatus.ALLOWED_ADVISORY) -> EvidenceRequest:
    return EvidenceRequest(
        request_id=f"REQ-{target}",
        type=EvidenceRequestType.MEASUREMENT,
        target=target,
        instruction=f"Measure {target}.",
        reason="This differentiates the hypotheses.",
        safety_status=safety,
    )


def test_selector_prefers_candidate_that_tests_more_hypotheses() -> None:
    candidates = [
        rank_candidate(
            make_request("discharge pressure"),
            supported_by_documentation=True,
            discriminates_hypotheses=["H1", "H2"],
            observations=[],
            previous_requests=[],
        ),
        rank_candidate(
            make_request("oil level"),
            supported_by_documentation=True,
            discriminates_hypotheses=["H1"],
            observations=[],
            previous_requests=[],
        ),
    ]

    selected = select_next_evidence(candidates)

    assert selected is not None
    assert selected.candidate == "discharge pressure"


def test_selector_excludes_already_requested_and_blocked_candidates() -> None:
    requested = make_request("discharge pressure")
    candidates = [
        rank_candidate(
            requested,
            supported_by_documentation=True,
            discriminates_hypotheses=["H1", "H2"],
            observations=[],
            previous_requests=[requested],
        ),
        rank_candidate(
            make_request("open pressure vessel", SafetyStatus.SAFETY_BLOCK),
            supported_by_documentation=True,
            discriminates_hypotheses=["H1", "H2"],
            observations=[],
            previous_requests=[],
        ),
    ]

    assert select_next_evidence(candidates) is None
