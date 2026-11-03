import pytest

from backend.app.diagnostics.playbooks import PILOT_FAULTS, Playbook, PlaybookEngine
from backend.app.models import AssetContext, GroundedSource
from backend.tests.test_retrieval import make_chunks
from ingestion.retrieval import TfidfIndex


def fixture_engine(fault, safety="ALLOWED_ADVISORY"):
    # Entirely synthetic contract evidence; no industrial procedure is asserted.
    chunks = make_chunks(model="fixture", revision="R1")
    chunks[0].text = " ".join(t for terms in PILOT_FAULTS.values() for t in terms)
    source = GroundedSource(chunk_id="chunk-a", document_id="doc-1", page=5,
                            section="Introduction", supporting_text=chunks[0].text)
    playbook = Playbook(
        id="fixture-rule", fault=fault, manufacturer="DOE", model="fixture", revision="R1",
        approved_by="test-only", approval_reference="synthetic-fixture", source=source,
        hypothesis="Synthetic hypothesis for software tests only.",
        evidence_request=dict(request_id="fixture-request", type="technician_report",
            target="fixture display", instruction="Describe the fixture display.",
            reason="Synthetic evidence collection.", source_references=[source], safety_status=safety),
    )
    return PlaybookEngine(TfidfIndex(chunks), [playbook]), AssetContext(
        manufacturer="DOE", model="fixture", revision="R1", equipment_family="compressed air systems",
    )


@pytest.mark.parametrize("fault", list(PILOT_FAULTS))
def test_five_faults_produce_only_source_bound_requests(fault):
    engine, asset = fixture_engine(fault)
    result = engine.assess(asset, PILOT_FAULTS[fault][0])
    assert result.status.value == "NEED_EVIDENCE"
    assert result.next_evidence_request.source_references
    repeated = engine.assess(asset, PILOT_FAULTS[fault][0], previous_requests=[result.next_evidence_request])
    assert repeated.status.value == "ESCALATE"
    assert repeated.next_evidence_request is None


@pytest.mark.parametrize("safety,status", [("UNKNOWN", "ESCALATE"),
    ("REQUIRES_SUPERVISION", "ESCALATE"), ("SAFETY_BLOCK", "SAFETY_BLOCK")])
def test_restricted_requests_never_reach_technician(safety, status):
    engine, asset = fixture_engine("fails_to_start", safety)
    result = engine.assess(asset, "fails to start")
    assert result.status.value == status
    assert result.next_evidence_request is None


def test_no_approved_playbook_escalates():
    engine, asset = fixture_engine("fails_to_start")
    engine.playbooks = []
    assert engine.assess(asset, "fails to start").status.value == "ESCALATE"
