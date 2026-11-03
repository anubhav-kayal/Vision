from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest

from backend.app.runtime import create_runtime


def test_runtime_starts_against_migrated_database_and_restarts(tmp_path, monkeypatch):
    monkeypatch.setenv("VISION_DATABASE_URL", f"sqlite:///{tmp_path / 'runtime.db'}")
    monkeypatch.setenv("VISION_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("VISION_API_TOKEN", "test-runtime-secret-123")
    monkeypatch.setenv("VISION_ENABLE_MODELS", "0")
    monkeypatch.delenv("VISION_RETRIEVAL", raising=False)
    command.upgrade(Config("alembic.ini"), "head")
    app = create_runtime()
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer test-runtime-secret-123"
        assert client.post("/api/v1/organizations", json=dict(id="persistent-org", name="Fixture")).status_code == 201
    app.state.engine.dispose()
    restarted = create_runtime()
    with TestClient(restarted) as client:
        client.headers["Authorization"] = "Bearer test-runtime-secret-123"
        assert client.post("/api/v1/sites", json=dict(
            id="persistent-site", name="Fixture", organization_id="persistent-org",
        )).status_code == 201


def test_runtime_requires_token(monkeypatch):
    monkeypatch.delenv("VISION_API_TOKEN", raising=False)
    with pytest.raises(ValueError, match="VISION_API_TOKEN"):
        create_runtime()
