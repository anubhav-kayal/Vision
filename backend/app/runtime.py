"""Run with uvicorn backend.app.runtime:create_runtime --factory --host 127.0.0.1."""

import json
import os
from pathlib import Path

from backend.app.catalog_service import CatalogService
from backend.app.diagnostics.playbooks import Playbook
from backend.app.image_workflow import ImageWorkflow, LocalObjectStore
from backend.app.persistence import database
from backend.app.pilot_api import pilot_app
from backend.app.pilot_service import PilotDiagnostics
from backend.app.sql_repositories import SqlCatalog, SqlDiagnosticSessionRepository


def create_runtime():
    token = os.environ.get("VISION_API_TOKEN", "")
    if len(token) < 16:
        raise ValueError("set VISION_API_TOKEN to at least 16 characters")
    root = Path(os.environ.get("VISION_DATA_DIR", ".runtime")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    url = os.environ.get("VISION_DATABASE_URL", f"sqlite:///{root / 'pilot.db'}")
    # Migration is explicit: startup must not silently mutate a database schema.
    engine, sessions = database(url)
    catalog = CatalogService(SqlCatalog(sessions))
    playbooks_path = os.environ.get("VISION_PLAYBOOKS")
    playbooks = [Playbook.model_validate(row) for row in json.loads(
        Path(playbooks_path).read_text())] if playbooks_path else []
    provider, embeddings = None, None
    if os.environ.get("VISION_ENABLE_MODELS") == "1":
        from openai import OpenAI
        from backend.app.openai_provider import OpenAIEmbeddings, OpenAIProvider
        client = OpenAI(timeout=30, max_retries=1)
        provider = OpenAIProvider(client, model=os.environ.get("VISION_MODEL", "gpt-6.1-sol"))
        embeddings = OpenAIEmbeddings(client)
    channel_factory, indexer = None, None
    if os.environ.get("VISION_RETRIEVAL") == "postgres":
        if engine.dialect.name != "postgresql":
            raise ValueError("Postgres retrieval requires a PostgreSQL database")
        from ingestion.hybrid import HybridIndex
        from ingestion.postgres import PostgresChannel, index_document
        vector = embeddings if os.environ.get("VISION_ENABLE_VECTOR") == "1" else None
        def channel_factory(asset):
            registered = catalog.require("assets", asset.asset_id)
            lexical = PostgresChannel(engine, catalog.repository, registered.site_id)
            semantic = PostgresChannel(engine, catalog.repository, registered.site_id, embeddings=vector) if vector else None
            return HybridIndex(lexical, semantic, min_lexical_score=0)
        indexer = lambda record: index_document(sessions, record, vector)
    diagnostics = PilotDiagnostics(catalog, SqlDiagnosticSessionRepository(sessions),
                                   playbooks, provider, channel_factory)
    objects = LocalObjectStore(root / "objects")
    images = ImageWorkflow(sessions, diagnostics, objects, provider)
    app = pilot_app(diagnostics, catalog, images, objects, token, indexer)
    app.state.engine = engine
    return app
