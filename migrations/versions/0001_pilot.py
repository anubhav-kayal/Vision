"""Initial pilot catalog, sessions, and image evidence schema."""
from alembic import op
from backend.app.persistence import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(op.get_bind())


def downgrade():
    Base.metadata.drop_all(op.get_bind())
