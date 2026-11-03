"""Full text search table; vector extension explicitly enabled only on PostgreSQL."""
import os
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("search_chunks", sa.Column("id", sa.String, primary_key=True),
                    sa.Column("site_id", sa.String, nullable=False),
                    sa.Column("revision_id", sa.String, nullable=False),
                    sa.Column("body", sa.Text, nullable=False),
                    sa.Column("payload", sa.JSON, nullable=False))
    op.create_index("ix_search_chunks_site_id", "search_chunks", ["site_id"])
    op.create_index("ix_search_chunks_revision_id", "search_chunks", ["revision_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE INDEX search_text_idx ON search_chunks USING GIN (to_tsvector('english', body))")
        if os.environ.get("VISION_ENABLE_VECTOR") == "1":
            from pgvector.sqlalchemy import Vector
            op.execute("CREATE EXTENSION IF NOT EXISTS vector")
            op.create_table("chunk_embeddings", sa.Column("id", sa.String, primary_key=True),
                            sa.Column("model", sa.String, nullable=False),
                            sa.Column("embedding", Vector(1536), nullable=False))


def downgrade():
    if sa.inspect(op.get_bind()).has_table("chunk_embeddings"):
        op.drop_table("chunk_embeddings")
    op.drop_table("search_chunks")
