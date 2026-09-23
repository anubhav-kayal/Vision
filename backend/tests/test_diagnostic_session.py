from backend.app.diagnostics.engine import DiagnosticEngineV0
from backend.app.diagnostics.models import (
    DiagnosticSession,
    DiagnosticStatus,
    EvidenceRequest,
    EvidenceRequestType,
    HypothesisStatus,
    Observation,
)
from backend.app.diagnostics.session import DiagnosticSessionService
from backend.app.models import Asset
from backend.tests.test_diagnostic_engine import make_engine


def make_session() -> DiagnosticSession:
    return DiagnosticSession(
        session_id="SESSION-001",
        asset=Asset(
            asset_id="ASSET-001",
            manufacturer="Example OEM",
            equipment_family="compressed air systems",
            model="X200",
        ),
        reported_problem="high discharge temperature",
    )


def temperature(value: float, observation_id: str = "OBS-TEMP") -> Observation:
    return Observation(
        observation_id=observation_id,
        type="measurement",
        parameter="discharge_temperature",
        value=value,
        unit="C",
        source="manual_entry",
    )


def test_two_turn_loop_records_request_and_observation() -> None:
    service = DiagnosticSessionService(make_engine())
    session, first = service.assess(make_session())
    assert first.next_evidence_request is not None

    session = session.add_observation(temperature(108))
    session, second = service.assess(session)

    assert len(session.observations) == 1
    assert session.status is DiagnosticStatus.NEED_EVIDENCE
    assert second.next_evidence_request is not None
    assert len(session.evidence_requests) == 2


def test_three_turn_loop_updates_hypotheses_and_avoids_duplicate_request() -> None:
    service = DiagnosticSessionService(make_engine())
    session, _ = service.assess(make_session())
    session = session.add_observation(temperature(108))
    session, _ = service.assess(session)
    session = session.add_observation(
        Observation(
            observation_id="OBS-VISUAL",
            type="visual",
            parameter="cooling_surfaces",
            value="cooling surfaces are dirty and airflow is restricted",
            source="manual_entry",
        )
    )
    session, assessment = service.assess(session)

    assert len(session.observations) == 2
    assert session.status is DiagnosticStatus.DIAGNOSIS_SUPPORTED
    assert assessment.next_evidence_request is None
    assert any(h.status is HypothesisStatus.SUPPORTED for h in session.hypotheses)


def test_contradictory_clean_observation_marks_hypotheses_contradicted() -> None:
    service = DiagnosticSessionService(make_engine())
    session = make_session().add_observation(temperature(108))
    session, _ = service.assess(session)
    session = session.add_observation(
        Observation(
            observation_id="OBS-VISUAL",
            type="visual",
            parameter="cooling_surfaces",
            value="cooling surfaces are clean and airflow is normal",
            source="manual_entry",
        )
    )
    session, _ = service.assess(session)

    assert all(h.status is HypothesisStatus.CONTRADICTED for h in session.hypotheses)


def test_corrected_observation_preserves_original_history() -> None:
    session = make_session().add_observation(
        Observation(
            observation_id="OBS-PRESSURE-1",
            type="measurement",
            parameter="pressure",
            value=2,
            unit="bar",
            source="manual_entry",
        )
    )
    session = session.add_observation(
        Observation(
            observation_id="OBS-PRESSURE-2",
            type="measurement",
            parameter="pressure",
            value=5.8,
            unit="bar",
            source="manual_entry",
            supersedes_observation_id="OBS-PRESSURE-1",
            correction_reason="Technician corrected the initial entry.",
        )
    )

    assert len(session.observations) == 2
    assert session.observations[0].superseded_by_observation_id == "OBS-PRESSURE-2"
    assert [item.observation_id for item in session.active_observations()] == ["OBS-PRESSURE-2"]
