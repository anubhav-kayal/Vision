import json

from backend.app.grounded_answering import GroundedAnswerGenerator, build_grounded_prompt
from backend.app.models import AnswerStatus, AuthorityLevel
from ingestion.retrieval import RetrievedChunk


def make_result() -> RetrievedChunk:
    return RetrievedChunk(
        score=0.9,
        chunk_id="chunk-1",
        document_id="doc-1",
        page=5,
        printed_page="5",
        section="Introduction",
        text="Positive displacement and dynamic compressors are two basic compressor types.",
        metadata={"authority_level": AuthorityLevel.GOVERNMENT_TECHNICAL_GUIDE.value},
    )


class FakeProvider:
    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.calls = 0
        self.last_user_prompt = ""

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        self.last_user_prompt = user_prompt
        return self.payload


def test_prompt_contains_only_retrieved_context() -> None:
    prompt = build_grounded_prompt("What are the compressor types?", [make_result()])

    assert "chunk-1" in prompt
    assert "Positive displacement" in prompt
    assert "unretrieved secret" not in prompt


def test_supported_answer_requires_matching_source_excerpt() -> None:
    provider = FakeProvider(
        json.dumps(
            {
                "status": "SUPPORTED",
                "answer": "The document identifies positive-displacement and dynamic compressors.",
                "sources": [
                    {
                        "chunk_id": "chunk-1",
                        "document_id": "doc-1",
                        "page": "5",
                        "section": "Introduction",
                        "supporting_text": "Positive displacement and dynamic compressors are two basic compressor types.",
                    }
                ],
                "evidence_summary": "The retrieved chunk names both types.",
            }
        )
    )

    answer = GroundedAnswerGenerator(provider).answer("What are the compressor types?", [make_result()])

    assert answer.status is AnswerStatus.SUPPORTED
    assert answer.sources[0].chunk_id == "chunk-1"
    assert provider.calls == 1


def test_unknown_source_is_rejected_conservatively() -> None:
    provider = FakeProvider(
        json.dumps(
            {
                "status": "SUPPORTED",
                "answer": "Unsupported claim.",
                "sources": [
                    {
                        "chunk_id": "not-retrieved",
                        "document_id": "doc-1",
                        "page": "5",
                        "section": "Introduction",
                        "supporting_text": "Unsupported claim.",
                    }
                ],
            }
        )
    )

    answer = GroundedAnswerGenerator(provider).answer("Question", [make_result()])

    assert answer.status is AnswerStatus.INSUFFICIENT_KNOWLEDGE
    assert answer.sources == []


def test_no_retrieved_evidence_does_not_call_provider() -> None:
    provider = FakeProvider("{}"); answer = GroundedAnswerGenerator(provider).answer("Question", [])

    assert answer.status is AnswerStatus.INSUFFICIENT_KNOWLEDGE
    assert provider.calls == 0
