"""Local pilot corpus: exact asset identity, current revision and authority checks."""

from backend.app.models import AuthorityLevel
from ingestion.retrieval import TfidfIndex


class ApplicableCorpus:
    strategy = "asset_filtered_tfidf"

    def __init__(self, catalog, asset_id):
        self.catalog, self.asset_id = catalog, asset_id

    def retrieve(self, query, *, top_k=5, asset_context=None):
        from backend.app.catalog_service import CatalogService
        registered = self.catalog.get("assets", self.asset_id)
        if not registered or not asset_context:
            return []
        asset = registered.asset
        if any(not getattr(asset_context, k) or getattr(asset_context, k) != getattr(asset, k)
               for k in ("manufacturer", "equipment_family", "model", "revision")):
            return []
        records = [r for r in self.catalog.list("documents")
                   if r.asset_id == self.asset_id and r.site_id == registered.site_id
                   and r.status.value == "READY" and r.parsed
                   and CatalogService.applies(r, registered)]
        # A sourcebook or historical note cannot authorize model-specific assessment.
        authoritative = {AuthorityLevel.SAFETY_INSTRUCTION, AuthorityLevel.OEM_SERVICE_MANUAL,
                         AuthorityLevel.OEM_SERVICE_BULLETIN, AuthorityLevel.APPROVED_INTERNAL_SOP}
        records = [r for r in records if r.document.authority_level in authoritative]
        identities = [(r.document.document_id, r.document.revision) for r in records]
        if len(identities) != len(set(identities)):
            return []
        chunks = [c for r in records for c in r.parsed.chunks]
        return TfidfIndex(chunks).retrieve(query, top_k=top_k, asset_context=asset_context) if chunks else []
