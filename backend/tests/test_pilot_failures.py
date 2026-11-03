import pytest

from backend.app.providers import ProviderFailure
from backend.tests.test_playbooks import fixture_engine


@pytest.mark.parametrize("failure", ["refusal", "malformed", "invented"])
def test_provider_failure_escalates_without_instructions(failure):
    class Provider:
        def assess(self, _):
            if failure == "refusal":
                raise ProviderFailure("refused")
            if failure == "malformed":
                return {"unsafe_instruction": "invented"}
            return dict(hypotheses=[dict(label="fixture", description="fixture",
                support_level="SUPPORTED", evidence_ids=[], source_chunk_ids=["invented"])],
                evidence_summary="fixture")
    engine, asset = fixture_engine("fails_to_start")
    engine.provider = Provider()
    result = engine.assess(asset, "fails to start")
    assert result.status.value == "ESCALATE"
    assert result.next_evidence_request is None


def test_restricted_work_and_conflicting_faults_escalate():
    engine, asset = fixture_engine("fails_to_start")
    assert engine.assess(asset, "fails to start bypass interlock").status.value == "SAFETY_BLOCK"
    assert engine.assess(asset, "fails to start low voltage").status.value == "ESCALATE"
