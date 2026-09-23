import pytest

from backend.app.diagnostics.application import DiagnosticApplicationService
from backend.app.diagnostics.models import Observation, ObservationType
from backend.app.diagnostics.repository import InMemoryDiagnosticSessionRepository
from backend.app.models import Asset
from backend.tests.test_diagnostic_engine import make_engine


def make_service() -> DiagnosticApplicationService:
    return DiagnosticApplicationService(make_engine(), InMemoryDiagnosticSessionRepository())


def make_asset() -> Asset:
    return Asset(
        asset_id="ASSET-X200",
        manufacturer="Generic OEM",
        equipment_family="compressed air systems",
        model="X200",
        revision="R2",
    )


def test_application_service_creates_and_reassesses_session() -> None:
    service = make_service()
    session, first = service.create_session(
        session_id="SESSION-001",
        asset=make_asset(),
        reported_problem="High discharge temperature",
    )

    assert session.status.value == "NEED_EVIDENCE"
    assert first.next_evidence_request is not None
    assert service.get_session("SESSION-001").session_id == "SESSION-001"

    updated, second = service.add_observation(
        "SESSION-001",
        Observation(
            observation_id="OBS-001",
            type=ObservationType.MEASUREMENT,
            parameter="discharge_temperature",
            value=108,
            unit="C",
            source="manual_entry",
        ),
    )
    assert len(updated.observations) == 1
    assert second.next_evidence_request is not None


def test_application_service_does_not_leak_mutable_repository_state() -> None:
    service = make_service()
    session, _ = service.create_session(
        session_id="SESSION-002",
        asset=make_asset(),
        reported_problem="High discharge temperature",
    )
    session.observations.append(
        Observation(
            observation_id="LOCAL-ONLY",
            type=ObservationType.VISUAL,
            parameter="cooling_surfaces",
            value="dirty",
            source="manual_entry",
        )
    )
    assert service.get_session("SESSION-002").observations == []


def test_application_service_rejects_unknown_session() -> None:
    service = make_service()
    with pytest.raises(KeyError, match="SESSION-MISSING"):
        service.get_session("SESSION-MISSING")
