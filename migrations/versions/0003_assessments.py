"""Preserve complete assessment evidence alongside session state."""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("diagnostic_assessments", sa.Column("id", sa.String, primary_key=True),
                    sa.Column("session_id", sa.String, sa.ForeignKey("diagnostic_sessions.id"), nullable=False),
                    sa.Column("payload", sa.JSON, nullable=False))
    op.create_index("ix_diagnostic_assessments_session_id", "diagnostic_assessments", ["session_id"])


def downgrade():
    op.drop_table("diagnostic_assessments")
