from backend.app.models import AuthorityLevel, KnowledgeDocument
from ingestion.chunking import fixed_size_chunks, section_aware_chunks
from ingestion.models import ParsedPage


def make_document() -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id="doc-1",
        manufacturer="OEM",
        equipment_family="compressor",
        document_type="manual",
        authority_level=AuthorityLevel.OEM_SERVICE_MANUAL,
        source="https://example.test/manual.pdf",
    )


def test_section_aware_chunking_retains_heading_and_page_provenance() -> None:
    page = ParsedPage(
        pdf_page_number=284,
        printed_page_label="18-1",
        text="MAINTENANCE – AIR COMPRESSOR\nGENERAL\nCheck the oil level.\nAIR CLEANER\nInspect the indicator.",
        sections=["MAINTENANCE – AIR COMPRESSOR", "GENERAL", "AIR CLEANER"],
    )

    chunks = section_aware_chunks([page], make_document())

    assert chunks[0].section == "GENERAL"
    assert chunks[0].pdf_page_number == 284
    assert chunks[0].printed_page_label == "18-1"
    assert any(chunk.section == "AIR CLEANER" for chunk in chunks)


def test_fixed_size_chunking_is_bounded_and_deterministic() -> None:
    page = ParsedPage(pdf_page_number=1, text="abcdefghij")
    chunks = fixed_size_chunks([page], make_document(), max_chars=6, overlap=2)

    assert [chunk.text for chunk in chunks] == ["abcdef", "efghij"]
    assert all(chunk.chunking_strategy == "fixed_size" for chunk in chunks)
