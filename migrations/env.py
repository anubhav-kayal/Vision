import os

from alembic import context
from sqlalchemy import create_engine

from backend.app.persistence import Base

url = os.environ.get("VISION_DATABASE_URL", context.config.get_main_option("sqlalchemy.url"))
engine = create_engine(url)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
