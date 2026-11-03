"""PostgreSQL full-text and optional pgvector channels for a site-bound corpus."""

from math import isfinite
from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, String, Text, bindparam, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.persistence import Base
from ingestion.retrieval import TfidfIndex


class SearchChunk(Base):
    __tablename__ = "search_chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    site_id: Mapped[str] = mapped_column(String, index=True)
    revision_id: Mapped[str] = mapped_column(String, index=True)
    body: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON)


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    model: Mapped[str]
    embedding: Mapped[list] = mapped_column(Vector(1536))


class PostgresChannel:
    def __init__(self, engine, catalog, site_id, *, embeddings=None):
        self.engine, self.catalog, self.site_id = engine, catalog, site_id
        self.embeddings = embeddings

    def retrieve(self, query, *, top_k=5, asset_context=None):
        from ingestion.models import DocumentChunk
        if not query.strip() or top_k <= 0:
            raise ValueError("invalid search")
        eligible = [record for record in self.catalog.list("documents")
                    if record.site_id == self.site_id and record.status.value == "READY"
                    and asset_context and asset_context.model and asset_context.revision
                    and TfidfIndex._document_applies(record.document, asset_context)]
        ids = [record.id for record in eligible]
        if not ids:
            return []
        params = dict(site=self.site_id, ids=ids, query=query, limit=top_k)
        if self.embeddings:
            vector = self.embeddings.embed([query])[0]
            if len(vector) != 1536 or not all(isfinite(x) for x in vector):
                raise ValueError("invalid embedding dimensions or values")
            params.update(vector=str(vector), model=self.embeddings.model)
            sql = """SELECT c.payload, 1-(e.embedding <=> CAST(:vector AS vector)) AS score
                FROM search_chunks c JOIN chunk_embeddings e ON c.id=e.id
                WHERE c.site_id=:site AND c.revision_id IN :ids AND e.model=:model
                ORDER BY e.embedding <=> CAST(:vector AS vector), c.id LIMIT :limit"""
        else:
            sql = """SELECT c.payload,
                ts_rank_cd(to_tsvector('english', c.body), plainto_tsquery('english', :query)) AS score
                FROM search_chunks c WHERE c.site_id=:site AND c.revision_id IN :ids
                AND to_tsvector('english', c.body) @@ plainto_tsquery('english', :query)
                ORDER BY score DESC, c.id LIMIT :limit"""
        statement = text(sql).bindparams(bindparam("ids", expanding=True))
        with self.engine.connect() as connection:
            return [TfidfIndex._result(row.score, DocumentChunk.model_validate(row.payload))
                    for row in connection.execute(statement, params)]


def index_document(sessions, record, embeddings=None):
    if record.status.value != "READY" or not record.parsed:
        raise ValueError("only ready documents can be indexed")
    vectors = embeddings.embed([c.text for c in record.parsed.chunks]) if embeddings else None
    if vectors is not None and (len(vectors) != len(record.parsed.chunks)
            or any(len(v) != 1536 or not all(isfinite(x) for x in v) for v in vectors)):
        raise ValueError("invalid embeddings")
    with sessions.begin() as session:
        for i, chunk in enumerate(record.parsed.chunks):
            key = f"{record.id}:{chunk.chunk_id}"
            session.merge(SearchChunk(id=key, site_id=record.site_id, revision_id=record.id,
                                      body=chunk.text, payload=chunk.model_dump(mode="json")))
            if vectors is not None:
                session.merge(ChunkEmbedding(id=key, model=embeddings.model, embedding=vectors[i]))
