"""Opt-in: run only against an explicitly supplied disposable pilot test database."""

import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

URL = os.environ.get("VISION_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="VISION_TEST_DATABASE_URL is not configured")


def test_postgres_full_text_vector_and_asset_filter(monkeypatch):
    from backend.app.catalog import DocumentRecord, Organization, RegisteredAsset, Site
    from backend.app.catalog_service import CatalogService
    from backend.app.knowledge import IngestionService
    from backend.app.models import Asset, AssetContext, KnowledgeDocument
    from backend.app.persistence import database
    from backend.app.sql_repositories import SqlCatalog
    from ingestion.models import ParsedPage
    from ingestion.postgres import PostgresChannel, index_document

    monkeypatch.setenv("VISION_DATABASE_URL", URL)
    monkeypatch.setenv("VISION_ENABLE_VECTOR", "1")
    command.upgrade(Config("alembic.ini"), "head")
    engine, sessions = database(URL)
    catalog = CatalogService(SqlCatalog(sessions))
    prefix = uuid4().hex
    catalog.create("organizations", Organization(id=prefix, name="Synthetic test"))
    catalog.create("sites", Site(id=prefix, name="Synthetic test", organization_id=prefix))
    asset = Asset(asset_id=prefix, manufacturer="Synthetic OEM", equipment_family="fixture",
                  model="synthetic-model", revision="R1")
    catalog.create("assets", RegisteredAsset(site_id=prefix, asset=asset))
    doc = KnowledgeDocument(document_id=prefix, manufacturer=asset.manufacturer,
        equipment_family=asset.equipment_family, model=asset.model, revision="R1",
        document_type="synthetic_fixture", authority_level="current_oem_service_manual",
        source="fixture://not-an-industrial-manual")
    catalog.create("documents", DocumentRecord(id=prefix, site_id=prefix, asset_id=prefix, document=doc))
    record = IngestionService(catalog, lambda _: [ParsedPage(
        pdf_page_number=1, text="Synthetic fixture generator fails to start display report.",
    )]).ingest(prefix, "synthetic")

    class Embeddings:
        model = "synthetic-unit-vector"
        def embed(self, texts):
            return [[1.0] + [0.0] * 1535 for _ in texts]

    embeddings = Embeddings()
    index_document(sessions, record, embeddings)
    context = AssetContext.from_asset(asset)
    lexical = PostgresChannel(engine, catalog.repository, prefix)
    semantic = PostgresChannel(engine, catalog.repository, prefix, embeddings=embeddings)
    assert lexical.retrieve("generator start", asset_context=context)[0].document_id == prefix
    assert semantic.retrieve("generator start", asset_context=context)[0].score == pytest.approx(1.0)
    wrong = context.model_copy(update={"model": "wrong-model"})
    assert lexical.retrieve("generator start", asset_context=wrong) == []
    assert semantic.retrieve("generator start", asset_context=wrong) == []
    other_site = PostgresChannel(engine, catalog.repository, "other-site")
    assert other_site.retrieve("generator start", asset_context=context) == []
    engine.dispose()
