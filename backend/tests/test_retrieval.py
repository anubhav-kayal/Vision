from backend.app.models import AssetContext, AuthorityLevel, KnowledgeDocument
from ingestion.models import DocumentChunk
from ingestion.retrieval import TfidfIndex, tokenize


def make_chunks(model: str | None = None, revision: str | None = None) -> list[DocumentChunk]:
    document = KnowledgeDocument(
        document_id="doc-1",
        manufacturer="DOE",
        equipment_family="compressed air systems",
        model=model,
        revision=revision,
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


def test_asset_context_excludes_same_family_different_model() -> None:
    machine_a = make_chunks(model="A-100")
    machine_b = make_chunks(model="B-200")
    index = TfidfIndex(machine_a + machine_b)

    results = index.retrieve(
        "basic compressor types",
        asset_context=AssetContext(
            manufacturer="DOE",
            equipment_family="compressed air systems",
            model="A-100",
        ),
        top_k=10,
    )

    assert results
    assert {result.document_id for result in results} == {"doc-1"}
    assert all(result.metadata["model"] == "A-100" for result in results)


def test_asset_context_excludes_same_model_different_revision() -> None:
    current = make_chunks(model="A-100", revision="R2")
    old = make_chunks(model="A-100", revision="R1")
    index = TfidfIndex(current + old)

    results = index.retrieve(
        "basic compressor types",
        asset_context=AssetContext(model="A-100", revision="R2"),
        top_k=10,
    )

    assert results
    assert {result.metadata["revision"] for result in results} == {"R2"}


def test_generic_family_guidance_remains_available_for_an_oem_asset() -> None:
    results = TfidfIndex(make_chunks()).retrieve(
        "basic compressor types",
        asset_context=AssetContext(
            manufacturer="Different OEM",
            equipment_family="compressed air systems",
            model="X200",
        ),
    )

    assert results
