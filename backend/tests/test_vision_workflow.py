import pytest

from backend.app.diagnostics.evidence import VisualObservationDraft
from backend.app.image_workflow import ImageWorkflow, LocalObjectStore
from backend.app.persistence import Base, database
from backend.app.providers import ProviderFailure
from backend.app.sql_repositories import SqlDiagnosticSessionRepository
from backend.app.diagnostics.application import DiagnosticApplicationService
from backend.tests.test_diagnostic_engine import make_engine
from backend.tests.test_diagnostic_application import make_asset
from backend.tests.test_image_workflow import png


@pytest.mark.parametrize("mode,reason", [
    ("usable", "CONFIRM_OBSERVATION"), ("unclear", "CLEARER_IMAGE_REQUIRED"),
    ("refused", "VISION_UNAVAILABLE_OR_INVALID"), ("wrong-id", "VISION_UNAVAILABLE_OR_INVALID"),
])
def test_vision_proposals_preserve_image_and_uncertainty(tmp_path, mode, reason):
    class Vision:
        def observe(self, evidence_id, image, media_type, asset_context):
            assert image == png()
            assert media_type == "image/png"
            if mode == "refused":
                raise ProviderFailure("refused")
            return VisualObservationDraft(
                evidence_id="wrong" if mode == "wrong-id" else evidence_id,
                description="Synthetic visible evidence.",
                image_quality="usable" if mode == "usable" else "unclear",
            )
    engine, sessions = database(f"sqlite:///{tmp_path / 'vision.db'}")
    Base.metadata.create_all(engine)
    diagnostics = DiagnosticApplicationService(make_engine(), SqlDiagnosticSessionRepository(sessions))
    diagnostics.create_session(session_id="vision", asset=make_asset(), reported_problem="hot")
    flow = ImageWorkflow(sessions, diagnostics, LocalObjectStore(tmp_path / "objects"), Vision())
    result = flow.upload("vision", png(), "image/png", "operator")
    assert result["reason"] == reason
    assert result["status"] == "NEED_EVIDENCE"
    assert diagnostics.get_session("vision").observations == []
    assert not result["confirmed"]
