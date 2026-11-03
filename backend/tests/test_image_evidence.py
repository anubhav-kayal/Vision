import pytest
from pydantic import ValidationError

from backend.app.diagnostics.evidence import (
    ImageEvidence, ObservationSource, VisualObservationDraft,
)
from backend.app.diagnostics.models import VerificationStatus


def image_data(**changes):
    data = dict(
        evidence_id="image-001", session_id="session-001", asset_id="asset-001",
        storage_key="sessions/session-001/image-001", content_sha256="a" * 64,
        media_type="image/jpeg", size_bytes=1234, uploaded_by="technician-001",
    )
    return data | changes


def test_image_metadata_round_trip_preserves_provenance():
    evidence = ImageEvidence(**image_data())
    restored = ImageEvidence.model_validate_json(evidence.model_dump_json())
    assert restored == evidence
    assert restored.asset_id == "asset-001"
    assert restored.uploaded_at.tzinfo is not None


@pytest.mark.parametrize("changes", [
    {"content_sha256": "not-a-hash"}, {"content_sha256": "a" * 63},
    {"media_type": "application/pdf"}, {"size_bytes": 0}, {"size_bytes": True},
    {"size_bytes": "1234"}, {"asset_id": " "}, {"session_id": ""},
    {"storage_key": " "}, {"uploaded_by": " "}, {"evidence_id": " "},
])
def test_invalid_image_metadata_rejected(changes):
    with pytest.raises(ValidationError):
        ImageEvidence(**image_data(**changes))


def test_model_observation_requires_confirmation():
    draft = VisualObservationDraft(evidence_id="image-001", description="Display is unreadable")
    assert draft.source_kind is ObservationSource.MODEL
    assert draft.verification_status is VerificationStatus.UNVERIFIED
    assert draft.requires_confirmation is True


@pytest.mark.parametrize("changes", [
    {"verification_status": "verified"}, {"verification_status": "technician_reported"},
    {"requires_confirmation": False}, {"requires_confirmation": 1},
    {"confidence": 0.87}, {"source_kind": "technician"},
    {"description": " "}, {"evidence_id": " "}, {"repair_instruction": "replace part"},
])
def test_model_cannot_promote_or_extend_observation(changes):
    data = dict(evidence_id="image-001", description="Display is unreadable") | changes
    with pytest.raises(ValidationError):
        VisualObservationDraft(**data)


@pytest.mark.parametrize("source", list(ObservationSource))
def test_observation_source_round_trip(source):
    assert ObservationSource(source.value) is source
