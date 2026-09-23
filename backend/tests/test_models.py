from datetime import date

import pytest
from pydantic import ValidationError

from backend.app.models import (
    AnswerStatus,
    Asset,
    AssetContext,
    AuthorityLevel,
    GroundedAnswer,
    GroundedSource,
    KnowledgeDocument,
)


def test_asset_defaults_configuration_to_empty_mapping() -> None:
    asset = Asset(
        asset_id="asset-001",
        manufacturer="Example OEM",
        family="Compressor",
        model="C-100",
    )

    assert asset.configuration == {}
    assert asset.equipment_family == "Compressor"


def test_asset_context_copies_identity_without_claiming_sensor_evidence() -> None:
    asset = Asset(
        asset_id="asset-001",
        manufacturer="Example OEM",
        equipment_family="Compressor",
        model="C-100",
        firmware_version="1.2.3",
        site="Plant A",
    )

    context = AssetContext.from_asset(asset)

    assert context.model == "C-100"
    assert context.firmware_version == "1.2.3"
    assert context.metadata == {}


def test_knowledge_document_preserves_authority_and_revision() -> None:
    document = KnowledgeDocument(
        document_id="doc-001",
        manufacturer="Example OEM",
        equipment_family="Compressor",
        model="C-100",
        document_type="service_manual",
        revision="Rev B",
        effective_date=date(2025, 1, 15),
        authority_level=AuthorityLevel.OEM_SERVICE_MANUAL,
        source="https://example.test/manual.pdf",
    )

    assert document.authority_level is AuthorityLevel.OEM_SERVICE_MANUAL
    assert document.revision == "Rev B"


def test_domain_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Asset(
            asset_id="asset-001",
            manufacturer="Example OEM",
            family="Compressor",
            model="C-100",
            unsupported_field="should fail",
        )


def test_grounded_answer_requires_provenance_for_provided_source() -> None:
    answer = GroundedAnswer(
        status=AnswerStatus.SUPPORTED,
        answer="The procedure specifies checking the inlet filter.",
        sources=[
            GroundedSource(
                document_id="doc-001",
                page=12,
                section="Troubleshooting",
                supporting_text="Check the inlet filter for blockage.",
            )
        ],
    )

    assert answer.sources[0].page == 12
    assert answer.status is AnswerStatus.SUPPORTED
