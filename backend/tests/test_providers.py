from types import SimpleNamespace as NS
import pytest

from backend.app.openai_provider import OpenAIProvider
from backend.app.providers import AssessmentDraft, ProviderFailure, validate_proposal


def test_structured_adapter_disables_storage_and_handles_refusal():
    calls = []
    def parse(**kwargs):
        calls.append(kwargs)
        return NS(status="completed", output_parsed=AssessmentDraft(hypotheses=[], evidence_summary=""))
    provider = OpenAIProvider(NS(responses=NS(parse=parse)))
    assert provider.assess("fixture evidence").hypotheses == []
    assert calls[0]["store"] is False
    assert calls[0]["text_format"] is AssessmentDraft
    provider.client.responses.parse = lambda **_: NS(status="incomplete", output_parsed=None)
    with pytest.raises(ProviderFailure):
        provider.assess("fixture")


def test_unknown_citations_fail_closed():
    proposal = AssessmentDraft(hypotheses=[dict(
        label="fixture", description="fixture", support_level="WEAKLY_SUPPORTED",
        evidence_ids=[], source_chunk_ids=["invented"],
    )], evidence_summary="fixture")
    with pytest.raises(ProviderFailure, match="UNGROUNDED_SOURCE"):
        validate_proposal(proposal, [], [])


def test_timeout_is_redacted():
    def parse(**_):
        raise TimeoutError("sensitive request")
    provider = OpenAIProvider(NS(responses=NS(parse=parse)))
    with pytest.raises(ProviderFailure, match="MODEL_UNAVAILABLE_OR_INVALID") as failure:
        provider.assess("fixture")
    assert "sensitive" not in str(failure.value)
