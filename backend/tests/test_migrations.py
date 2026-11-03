from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from backend.app.persistence import database


def test_migrations_upgrade_downgrade_and_upgrade(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    monkeypatch.setenv("VISION_DATABASE_URL", url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine, _ = database(url)
    assert {"assets", "document_revisions", "search_chunks"} <= set(inspect(engine).get_table_names())
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(config, "head")
    assert "image_evidence" in inspect(engine).get_table_names()
