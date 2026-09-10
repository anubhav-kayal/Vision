from backend.app.models import AuthorityLevel, KnowledgeDocument
from ingestion.models import DocumentChunk
from ingestion.retrieval import TfidfIndex, tokenize


def make_chunks() -> list[DocumentChunk]:
    document = KnowledgeDocument(
        document_id="doc-1",
        manufacturer="DOE",
        equipment_family="compressed air systems",
        document_type="sourcebook",
        authority_level=AuthorityLevel.GOVERNMENT_TECHNICAL_GUIDE,
        source="https://example.test/sourcebook.pdf",
    )
    return [
        DocumentChunk(
            chunk_id="chunk-a",
            document=document,
            pdf_page_number=5,
            printed_page_label="5",
            section="Introduction",
            text="Positive displacement and dynamic compressors are two basic compressor types.",
            chunking_strategy="section_aware",
        ),
        DocumentChunk(
            chunk_id="chunk-b",
            document=document,
            pdf_page_number=29,
            printed_page_label="29",
            section="Leaks",
            text="Ultrasonic instruments can locate compressed air leaks.",
            chunking_strategy="section_aware",
        ),
    ]


def test_tokenize_removes_common_words_but_keeps_technical_terms() -> None:
    assert tokenize("What are the compressor types?") == ["compressor", "types"]


def test_retrieval_returns_provenance_and_ranked_match() -> None:
    results = TfidfIndex(make_chunks()).retrieve("basic compressor types", top_k=1)

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-a"
    assert results[0].printed_page == "5"
    assert results[0].metadata["authority_level"] == "government_technical_guide"


def test_unseen_query_returns_no_results() -> None:
    assert TfidfIndex(make_chunks()).retrieve("hydraulic pump fault code") == []
