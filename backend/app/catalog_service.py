"""Pilot catalog service enforces ownership and immutable document revisions."""

from backend.app.catalog import CatalogRepository, DocumentRecord, RegisteredAsset
from backend.app.models import AssetStatus


class CatalogService:
    def __init__(self, repository: CatalogRepository):
        self.repository = repository

    def require(self, kind, identifier):
        value = self.repository.get(kind, identifier)
        if value is None:
            raise KeyError(f"{kind} not found: {identifier}")
        return value

    def create(self, kind, value):
        identifier = value.asset.asset_id if kind == "assets" else value.id
        if self.repository.get(kind, identifier):
            raise ValueError(f"duplicate {kind}: {identifier}")
        if kind == "sites":
            self.require("organizations", value.organization_id)
        elif kind in {"assets", "documents"}:
            self.require("sites", value.site_id)
        if kind == "assets" and value.asset.asset_status is AssetStatus.ASSET_CONFIRMED:
            raise ValueError("public registration cannot confirm asset identity")
        if kind == "documents":
            registered = self.require("assets", value.asset_id)
            if registered.site_id != value.site_id:
                raise ValueError("document and asset must belong to the same site")
            if not value.document.model or not value.document.revision:
                raise ValueError("pilot documents require model and revision")
            if not self.applies(value, registered):
                raise ValueError("document identity does not match the asset")
            if any(item.asset_id == value.asset_id and item.document == value.document
                   for item in self.repository.list("documents")):
                raise ValueError("duplicate document revision")
        self.repository.put(kind, identifier, value)
        return value

    @staticmethod
    def applies(record: DocumentRecord, registered: RegisteredAsset):
        doc, asset = record.document, registered.asset
        return all(getattr(asset, key) and getattr(doc, key)
                   and getattr(asset, key).casefold() == getattr(doc, key).casefold()
                   for key in ("manufacturer", "equipment_family", "model", "revision"))

    def update_asset(self, identifier, value):
        existing = self.require("assets", identifier)
        if value.asset.asset_id != identifier or value.site_id != existing.site_id:
            raise ValueError("asset ID and site cannot be changed")
        if value.asset.asset_status is AssetStatus.ASSET_CONFIRMED:
            raise ValueError("public update cannot confirm asset identity")
        self.repository.put("assets", identifier, value)
        return value

    def supersede(self, identifier):
        from backend.app.catalog import ProcessingStatus
        record = self.require("documents", identifier)
        if record.status is not ProcessingStatus.READY:
            raise ValueError("only ready documents can be superseded")
        record.status = ProcessingStatus.SUPERSEDED
        self.repository.put("documents", identifier, record)
        return record
