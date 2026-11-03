import pytest

from backend.app.catalog import DocumentRecord, MemoryCatalog, Organization, RegisteredAsset, Site
from backend.app.catalog_service import CatalogService
from backend.app.knowledge import IngestionService
from backend.app.persistence import Base, database
from backend.app.sql_repositories import SqlCatalog, SqlDiagnosticSessionRepository
from backend.app.models import Asset, KnowledgeDocument
from backend.tests.test_diagnostic_application import make_asset, make_service
from ingestion.models import ParsedPage


@pytest.fixture(params=["memory", "sql"])
def catalog(request, tmp_path):
    if request.param == "memory":
        repository = MemoryCatalog()
    else:
        engine, sessions = database(f"sqlite:///{tmp_path / 'catalog.db'}")
        Base.metadata.create_all(engine)
        repository = SqlCatalog(sessions)
    service = CatalogService(repository)
    service.create("organizations", Organization(id="org", name="Fixture organization"))
    service.create("sites", Site(id="site", name="Fixture site", organization_id="org"))
    service.create("assets", RegisteredAsset(site_id="site", asset=Asset(
        asset_id="asset", manufacturer="Fixture OEM", equipment_family="diesel_generator",
        model="fixture-model", revision="R1",
    )))
    return service


def record(**changes):
    doc = dict(document_id="manual", manufacturer="Fixture OEM",
               equipment_family="diesel_generator", model="fixture-model", revision="R1",
               document_type="service_manual", authority_level="current_oem_service_manual",
               source="fixture://manual") | changes
    return DocumentRecord(id="manual-r1", site_id="site", asset_id="asset",
                          document=KnowledgeDocument(**doc))


def test_catalog_ownership_and_defensive_copies(catalog):
    item = catalog.require("assets", "asset")
    item.asset.model = "local mutation"
    assert catalog.require("assets", "asset").asset.model == "fixture-model"
    with pytest.raises(ValueError, match="duplicate"):
        catalog.create("assets", catalog.require("assets", "asset"))
    with pytest.raises(KeyError):
        catalog.create("sites", Site(id="bad", name="bad", organization_id="missing"))


@pytest.mark.parametrize("changes", [{"model": "wrong"}, {"revision": "R2"}, {"model": None}])
def test_wrong_document_rejected(catalog, changes):
    with pytest.raises(ValueError):
        catalog.create("documents", record(**changes))


def test_ingestion_records_pages_and_refuses_reprocessing(catalog):
    catalog.create("documents", record())
    parser = lambda _: [ParsedPage(pdf_page_number=7, printed_page_label="5",
                                  text="Fixture evidence only.")]
    result = IngestionService(catalog, parser).ingest("manual-r1", "fixture.pdf")
    assert result.status.value == "READY"
    assert result.parsed.chunks[0].pdf_page_number == 7
    assert result.parsed.chunks[0].document.revision == "R1"
    with pytest.raises(ValueError):
        IngestionService(catalog, parser).ingest("manual-r1", "fixture.pdf")


def test_empty_document_rejected_with_reason(catalog):
    catalog.create("documents", record())
    result = IngestionService(catalog, lambda _: []).ingest("manual-r1", "empty.pdf")
    assert result.status.value == "REJECTED"
    assert result.failure_reason == "MANUAL_PARSE_FAILED"


def test_sql_session_survives_repository_restart(tmp_path):
    url = f"sqlite:///{tmp_path / 'sessions.db'}"
    engine, sessions = database(url)
    Base.metadata.create_all(engine)
    value, _ = make_service().create_session(
        session_id="persisted", asset=make_asset(), reported_problem="high temperature",
    )
    SqlDiagnosticSessionRepository(sessions).save(value)
    engine.dispose()
    engine, restarted = database(url)
    loaded = SqlDiagnosticSessionRepository(restarted).get("persisted")
    assert loaded == value
    loaded.reported_problem = "local mutation"
    assert SqlDiagnosticSessionRepository(restarted).get("persisted") == value
