"""Authenticated single-site pilot API. Binary uploads use raw request bodies."""

import hmac
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import Field
from starlette.concurrency import run_in_threadpool

from backend.app.api import create_app
from backend.app.catalog import DocumentRecord, Organization, RegisteredAsset, Site
from backend.app.image_workflow import MAX_IMAGE_BYTES
from backend.app.knowledge import IngestionService
from backend.app.models import DomainModel, KnowledgeDocument
from backend.app.pilot_service import technician_response


class DocumentRegistration(DomainModel):
    id: str = Field(min_length=1)
    site_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    document: KnowledgeDocument


class Confirmation(DomainModel):
    description: str = Field(min_length=1)
    parameter: str = Field(min_length=1)
    confirmed_by: str = Field(min_length=1)


async def bounded_body(request, limit):
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > limit:
            raise ValueError("upload exceeds size limit")
        data.extend(chunk)
    return bytes(data)


def pilot_app(diagnostics, catalog, images, objects, token, indexer=None):
    if len(token) < 16:
        raise ValueError("pilot API token must have at least 16 characters")
    app = create_app(diagnostics)

    @app.middleware("http")
    async def authenticate(request, call_next):
        if request.url.path not in {"/health", "/docs", "/openapi.json", "/redoc"} and not hmac.compare_digest(
            request.headers.get("authorization", ""), f"Bearer {token}",
        ):
            return JSONResponse(status_code=401, media_type="application/problem+json",
                                content=dict(title="Unauthorized", status=401, detail="Bearer token required"))
        return await call_next(request)

    original_openapi = app.openapi

    def openapi():
        schema = original_openapi()
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["PilotToken"] = {
            "type": "http", "scheme": "bearer",
        }
        schema["security"] = [{"PilotToken": []}]
        schema["paths"]["/health"]["get"]["security"] = []
        return schema

    app.openapi = openapi

    @app.exception_handler(KeyError)
    async def missing(_, exc):
        return JSONResponse(status_code=404, media_type="application/problem+json",
                            content=dict(title="Resource not found", status=404, detail=str(exc).strip("'")))

    @app.exception_handler(ValueError)
    async def invalid(_, exc):
        return JSONResponse(status_code=422, media_type="application/problem+json",
                            content=dict(title="Request rejected", status=422, detail=str(exc)))

    @app.post("/api/v1/organizations", status_code=201)
    def organization(value: Organization):
        return catalog.create("organizations", value)

    @app.get("/api/v1/diagnostic-sessions/{session_id}/history")
    def history(session_id: str):
        diagnostics.get_session(session_id)
        return diagnostics._repository.history(session_id)

    @app.post("/api/v1/sites", status_code=201)
    def site(value: Site):
        return catalog.create("sites", value)

    @app.post("/api/v1/assets", status_code=201)
    def asset(value: RegisteredAsset):
        return catalog.create("assets", value)

    @app.get("/api/v1/assets/{asset_id}")
    def get_asset(asset_id: str):
        return catalog.require("assets", asset_id)

    @app.put("/api/v1/assets/{asset_id}")
    def update_asset(asset_id: str, value: RegisteredAsset):
        return catalog.update_asset(asset_id, value)

    @app.post("/api/v1/documents", status_code=201)
    def document(value: DocumentRegistration):
        return catalog.create("documents", DocumentRecord(**value.model_dump()))

    @app.get("/api/v1/documents/{revision_id}")
    def get_document(revision_id: str):
        return catalog.require("documents", revision_id)

    @app.post("/api/v1/documents/{revision_id}/supersession")
    def supersede(revision_id: str):
        return catalog.supersede(revision_id)

    @app.put("/api/v1/documents/{revision_id}/content")
    async def content(revision_id: str, request: Request):
        catalog.require("documents", revision_id)
        data = await bounded_body(request, 20 * 1024 * 1024)
        if request.headers.get("content-type") != "application/pdf" or not data.startswith(b"%PDF-"):
            raise ValueError("PDF content required")
        key = uuid4().hex
        objects.put(key, data)
        record = await run_in_threadpool(IngestionService(catalog).ingest, revision_id, objects.path(key))
        if indexer and record.status.value == "READY":
            await run_in_threadpool(indexer, record)
        return record

    @app.post("/api/v1/diagnostic-sessions/{session_id}/images", status_code=201)
    async def upload(session_id: str, request: Request):
        data = await bounded_body(request, MAX_IMAGE_BYTES)
        return await run_in_threadpool(images.upload, session_id, data,
            request.headers.get("content-type"), request.headers.get("x-technician-id", "pilot-operator"))

    @app.post("/api/v1/diagnostic-sessions/{session_id}/images/{evidence_id}/confirmation")
    def confirm(session_id: str, evidence_id: str, value: Confirmation):
        session, assessment = images.confirm(session_id, evidence_id, **value.model_dump())
        return technician_response(session, assessment)

    return app
