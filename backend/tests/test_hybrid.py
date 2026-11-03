import pytest

from backend.app.corpus import ApplicableCorpus
from backend.app.models import AssetContext
from backend.tests.test_catalog import catalog, record
from backend.app.knowledge import IngestionService
from backend.app.catalog import ProcessingStatus
from ingestion.hybrid import HybridIndex
from ingestion.models import ParsedPage
from ingestion.retrieval import TfidfIndex
from backend.tests.test_retrieval import make_chunks


def test_hybrid_fusion_and_refusal():
    lexical = TfidfIndex(make_chunks())
    index = HybridIndex(lexical, lexical)
    assert index.retrieve("compressor types")[0].chunk_id == "chunk-a"
    assert index.retrieve("hydraulic pump") == []
    with pytest.raises(ValueError):
        index.retrieve(" ")


def test_corpus_requires_exact_current_asset_and_authority(catalog):
    catalog.create("documents", record())
    IngestionService(catalog, lambda _: [ParsedPage(
        pdf_page_number=1, text="Fixture controller alarm code.",
    )]).ingest("manual-r1", "fixture")
    asset = catalog.require("assets", "asset").asset
    context = AssetContext.from_asset(asset)
    corpus = ApplicableCorpus(catalog.repository, "asset")
    assert corpus.retrieve("controller alarm", asset_context=context)
    assert corpus.retrieve("controller alarm", asset_context=None) == []
    wrong = context.model_copy(update={"model": "other"})
    assert corpus.retrieve("controller alarm", asset_context=wrong) == []
    unknown = context.model_copy(update={"revision": None})
    assert corpus.retrieve("controller alarm", asset_context=unknown) == []
    doc = catalog.require("documents", "manual-r1")
    doc.status = ProcessingStatus.SUPERSEDED
    catalog.repository.put("documents", doc.id, doc)
    assert corpus.retrieve("controller alarm", asset_context=context) == []
