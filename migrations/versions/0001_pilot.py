"""Initial pilot catalog, sessions, and image evidence schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("organizations", sa.Column("id", sa.String, primary_key=True),
                    sa.Column("name", sa.String, nullable=False))
    op.create_table("sites", sa.Column("id", sa.String, primary_key=True),
                    sa.Column("name", sa.String, nullable=False),
                    sa.Column("organization_id", sa.String, sa.ForeignKey("organizations.id"), nullable=False))
    op.create_table("assets", sa.Column("id", sa.String, primary_key=True),
                    sa.Column("site_id", sa.String, sa.ForeignKey("sites.id"), nullable=False),
                    sa.Column("payload", sa.JSON, nullable=False))
    op.create_table("document_revisions", sa.Column("id", sa.String, primary_key=True),
                    sa.Column("site_id", sa.String, sa.ForeignKey("sites.id"), nullable=False),
                    sa.Column("asset_id", sa.String, sa.ForeignKey("assets.id"), nullable=False),
                    sa.Column("payload", sa.JSON, nullable=False))
    op.create_table("diagnostic_sessions", sa.Column("id", sa.String, primary_key=True),
                    sa.Column("payload", sa.JSON, nullable=False))
    op.create_table("image_evidence", sa.Column("id", sa.String, primary_key=True),
                    sa.Column("session_id", sa.String, sa.ForeignKey("diagnostic_sessions.id"), nullable=False),
                    sa.Column("payload", sa.JSON, nullable=False))


def downgrade():
    for table in ("image_evidence", "diagnostic_sessions", "document_revisions",
                  "assets", "sites", "organizations"):
        op.drop_table(table)
