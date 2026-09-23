from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from backend.app.diagnostics.models import (
    DiagnosticSession,
    DiagnosticStatus,
    EvidenceRequest,
    EvidenceRequestType,
    Hypothesis,
    Observation,
    ObservationType,
    SafetyStatus,
    SupportLevel,
    Symptom,
    VerificationStatus,
)
from backend.app.models import Asset


def make_asset() -> Asset:
    return Asset(
        asset_id="ASSET-001",
        manufacturer="Example OEM",
        equipment_family="compressor",
        model="X200",
    )


def test_symptom_is_distinct_from_verified_observation() -> None:
    symptom = Symptom(symptom_id="SYM-001", description="machine overheating", reported_by="tech")
    observation = Observation(
        observation_id="OBS-001",
        type=ObservationType.MEASUREMENT,
        parameter="discharge_temperature",
        value=108,
        unit="C",
        source="manual_entry",
        verification_status=VerificationStatus.TECHNICIAN_REPORTED,
    )

    assert symptom.confidence is None
    assert observation.verification_status is VerificationStatus.TECHNICIAN_REPORTED


def test_invalid_observation_type_and_unit_are_rejected() -> None:
    with pytest.raises(ValidationError, match="numeric value"):
        Observation(
            observation_id="OBS-001",
            type="measurement",
            parameter="temperature",
            value="hot",
            unit="C",
            source="manual_entry",
        )
    with pytest.raises(ValidationError, match="require a unit"):
        Observation(
            observation_id="OBS-002",
            type="measurement",
            parameter="temperature",
            value=108,
            source="manual_entry",
        )


def test_session_rejects_unknown_hypothesis_references() -> None:
    with pytest.raises(ValidationError, match="unknown observations"):
        DiagnosticSession(
            session_id="SESSION-001",
            asset=make_asset(),
            reported_problem="high discharge temperature",
            hypotheses=[
                Hypothesis(
                    hypothesis_id="HYP-001",
                    description="restricted cooling",
                    supporting_evidence=["OBS-MISSING"],
                )
            ],
        )


def test_session_round_trips_with_evidence_request_and_status() -> None:
    created = datetime(2026, 9, 13, tzinfo=UTC)
    session = DiagnosticSession(
        session_id="SESSION-001",
        asset=make_asset(),
        reported_problem="high discharge temperature",
        symptoms=[
            Symptom(symptom_id="SYM-001", description="overheating", reported_by="tech")
        ],
        observations=[
            Observation(
                observation_id="OBS-001",
                type="measurement",
                parameter="discharge_temperature",
                value=108,
                unit="C",
                source="manual_entry",
            )
        ],
        hypotheses=[
            Hypothesis(
                hypothesis_id="HYP-001",
                description="cooling restriction",
                supporting_evidence=["OBS-001"],
                support_level=SupportLevel.SUPPORTED,
            )
        ],
        evidence_requests=[
            EvidenceRequest(
                request_id="REQ-001",
                type=EvidenceRequestType.VISUAL,
                target="cooler exterior",
                instruction="Inspect the cooler exterior for dirt buildup.",
                reason="This observation can test the cooling-restriction hypothesis.",
                related_hypotheses=["HYP-001"],
                safety_status=SafetyStatus.ALLOWED_ADVISORY,
            )
        ],
        status=DiagnosticStatus.NEED_EVIDENCE,
        created_at=created,
        updated_at=created + timedelta(minutes=1),
    )

    restored = DiagnosticSession.model_validate_json(session.model_dump_json())

    assert restored.status is DiagnosticStatus.NEED_EVIDENCE
    assert restored.evidence_requests[0].related_hypotheses == ["HYP-001"]
