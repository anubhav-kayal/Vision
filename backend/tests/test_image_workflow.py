import io
import pytest
from PIL import Image

from backend.app.image_workflow import ImageWorkflow, LocalObjectStore
from backend.app.persistence import Base, database
from backend.app.sql_repositories import SqlDiagnosticSessionRepository
from backend.app.diagnostics.application import DiagnosticApplicationService
from backend.tests.test_diagnostic_engine import make_engine
from backend.tests.test_diagnostic_application import make_asset


def png():
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_image_confirmation_and_ownership(tmp_path):
    engine, sessions = database(f"sqlite:///{tmp_path / 'image.db'}")
    Base.metadata.create_all(engine)
    diagnostics = DiagnosticApplicationService(make_engine(), SqlDiagnosticSessionRepository(sessions))
    for identifier in ("one", "two"):
        diagnostics.create_session(session_id=identifier, asset=make_asset(), reported_problem="hot")
    flow = ImageWorkflow(sessions, diagnostics, LocalObjectStore(tmp_path / "objects"))
    uploaded = flow.upload("one", png(), "image/png", "technician")
    identifier = uploaded["metadata"]["evidence_id"]
    assert uploaded["reason"] == "VISION_NOT_CONFIGURED"
    with pytest.raises(KeyError):
        flow.get("two", identifier)
    updated, _ = flow.confirm("one", identifier, "display unreadable", "display", "technician")
    assert updated.observations[-1].verification_status.value == "technician_reported"
    with pytest.raises(ValueError):
        flow.confirm("one", identifier, "duplicate", "display", "technician")
    with pytest.raises(ValueError):
        flow.upload("one", b"not an image", "image/png", "technician")
    with pytest.raises(ValueError):
        flow.upload("one", png(), "image/jpeg", "technician")
    with pytest.raises(ValueError):
        flow.store.get("../escape")
