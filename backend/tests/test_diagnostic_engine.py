from backend.app.diagnostics.engine import DiagnosticEngineV0
from backend.app.diagnostics.models import DiagnosticStatus, Observation
from backend.app.models import AssetContext, AuthorityLevel, KnowledgeDocument
from ingestion.models import DocumentChunk
from ingestion.retrieval import TfidfIndex


def make_engine() -> DiagnosticEngineV0:
    document = KnowledgeDocument(
        document_id="doc-1",
        manufacturer="DOE",
        equipment_family="compressed air systems",
        model=None,
        document_type="sourcebook",
        authority_level=AuthorityLevel.GOVERNMENT_TECHNICAL_GUIDE,
        source="https://example.test/sourcebook.pdf",
    )
    chunks = [
        DocumentChunk(
            chunk_id="chunk-cooling",
            document=document,
            pdf_page_number=52,
            printed_page_label="52",
            section="Maintenance",
            text="Clean the cooling surfaces of the compressor and inspect air intake filters. Fouling can affect temperature.",
            chunking_strategy="section_aware",
        ),
        DocumentChunk(
            chunk_id="chunk-general",
            document=document,
            pdf_page_number=57,
            printed_page_label="57",
            section="Maintenance",
            text="Inspect the lubricant cooler and compressor components annually.",
            chunking_strategy="section_aware",
        ),
    ]
    return DiagnosticEngineV0(TfidfIndex(chunks))


def make_asset() -> AssetContext:
    return AssetContext(
        asset_id="ASSET-001",
        manufacturer="Example OEM",
        equipment_family="compressed air systems",
        model="X200",
    )


def test_engine_requests_measurement_before_diagnosing_temperature() -> None:
    assessment = make_engine().assess(make_asset(), "compressor overheating")

    assert assessment.status is DiagnosticStatus.NEED_EVIDENCE
    assert len(assessment.hypotheses) >= 2
    assert assessment.next_evidence_request is not None
    assert assessment.next_evidence_request.type.value == "measurement"
    assert assessment.retrieval is not None
    assert assessment.sources
    assert assessment.evidence_candidates[0].selection_reason


def test_engine_requests_discriminating_visual_observation_after_temperature() -> None:
    assessment = make_engine().assess(
        make_asset(),
        "high discharge temperature",
        observations=[
            Observation(
                observation_id="OBS-001",
                type="measurement",
                parameter="discharge_temperature",
                value=108,
                unit="C",
                source="manual_entry",
            )
        ],
    )

    assert assessment.status is DiagnosticStatus.NEED_EVIDENCE
    assert assessment.next_evidence_request.type.value == "visual"
    assert assessment.next_evidence_request.safety_status.value == "REQUIRES_SUPERVISION"
    assert all(h.support_level.value == "WEAKLY_SUPPORTED" for h in assessment.hypotheses)
    assert len(assessment.evidence_candidates) == 2


def test_engine_refuses_unsupported_problem_pattern() -> None:
    assessment = make_engine().assess(make_asset(), "hydraulic pump fault code")

    assert assessment.status is DiagnosticStatus.INSUFFICIENT_KNOWLEDGE
    assert assessment.next_evidence_request is None
