import pytest
from pydantic import ValidationError

from backend.app.catalog import ProcessingStatus
from backend.app.knowledge import IngestionService
from backend.tests.test_catalog import catalog, record  # noqa: F401 -- pytest fixture
from ingestion.models import ParsedPage


def test_asset_update_and_manual_retirement(catalog):
    registered = catalog.require("assets", "asset")
    registered.asset.controller_model = "fixture-controller"
    catalog.update_asset("asset", registered)
    assert catalog.require("assets", "asset").asset.controller_model == "fixture-controller"
    registered.site_id = "wrong-site"
    with pytest.raises(ValueError):
        catalog.update_asset("asset", registered)
    catalog.create("documents", record())
    IngestionService(catalog, lambda _: [ParsedPage(pdf_page_number=1, text="Fixture content.")]).ingest(
        "manual-r1", "fixture")
    assert catalog.supersede("manual-r1").status is ProcessingStatus.SUPERSEDED


def test_ready_records_require_matching_content():
    data = record().model_dump() | {"status": "READY"}
    with pytest.raises(ValidationError, match="parsed pages"):
        type(record()).model_validate(data)
