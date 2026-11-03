import pymupdf
import pytest
from fastapi.testclient import TestClient

from backend.app.catalog import DocumentRecord
from backend.app.diagnostics.playbooks import PILOT_FAULTS, Playbook
from backend.app.image_workflow import ImageWorkflow, LocalObjectStore
from backend.app.models import GroundedSource
from backend.app.persistence import Base, database
from backend.app.pilot_api import pilot_app
from backend.app.pilot_service import PilotDiagnostics
from backend.app.sql_repositories import SqlDiagnosticSessionRepository
from backend.tests.test_catalog import catalog
from backend.tests.test_image_workflow import png
from backend.tests.test_catalog import record
from backend.app.knowledge import IngestionService
from ingestion.models import ParsedPage


@pytest.fixture
def api(catalog, tmp_path):
    engine, sessions = database(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(engine)
    diagnostics = PilotDiagnostics(catalog, SqlDiagnosticSessionRepository(sessions))
    objects = LocalObjectStore(tmp_path / "objects")
    images = ImageWorkflow(sessions, diagnostics, objects)
    client = TestClient(pilot_app(diagnostics, catalog, images, objects, "test-pilot-token-123"))
    client.headers["Authorization"] = "Bearer test-pilot-token-123"
    return client, diagnostics, catalog


def create(client, catalog, problem="fails to start"):
    return client.post("/api/v1/diagnostic-sessions", json=dict(
        session_id="session", asset=catalog.require("assets", "asset").asset.model_dump(mode="json"),
        reported_problem=problem,
    ))


def test_auth_and_missing_documents(api):
    client, _, catalog = api
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/assets/asset", headers={"Authorization": "bad"}).status_code == 401
    response = create(client, catalog)
    assert response.status_code == 201
    assert response.json()["assessment"]["status"] == "INSUFFICIENT_KNOWLEDGE"
    assert create(client, catalog).status_code == 422
    assert client.get("/api/v1/assets/missing").status_code == 404


def test_manual_upload_and_image_confirmation(api):
    client, _, catalog = api
    registration = record().model_dump(mode="json", exclude={"status", "parsed", "failure_reason"})
    assert client.post("/api/v1/documents", json=registration).status_code == 201
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Synthetic fixture: generator fails to start. Record fixture display.")
    response = client.put("/api/v1/documents/manual-r1/content", content=pdf.tobytes(),
                          headers={"Content-Type": "application/pdf"})
    pdf.close()
    assert response.status_code == 200
    assert response.json()["status"] == "READY"
    assert create(client, catalog).status_code == 201
    response = client.post("/api/v1/diagnostic-sessions/session/images", content=png(),
                           headers={"Content-Type": "image/png"})
    assert response.status_code == 201
    identifier = response.json()["metadata"]["evidence_id"]
    confirmed = client.post(f"/api/v1/diagnostic-sessions/session/images/{identifier}/confirmation",
        json=dict(description="Fixture display unreadable", parameter="display", confirmed_by="operator"))
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "ESCALATE"
    assert confirmed.json()["escalation_reason"] == "NO_UNIQUE_APPROVED_PLAYBOOK"


@pytest.mark.parametrize("fault", list(PILOT_FAULTS))
def test_five_end_to_end_fault_paths(api, fault):
    client, diagnostics, catalog = api
    catalog.create("documents", record())
    content = "Synthetic fixture evidence: " + PILOT_FAULTS[fault][0]
    result = IngestionService(catalog, lambda _: [ParsedPage(pdf_page_number=1, text=content)]).ingest(
        "manual-r1", "fixture.pdf")
    chunk = result.parsed.chunks[0]
    source = GroundedSource(chunk_id=chunk.chunk_id, document_id="manual", page=1,
                            supporting_text=content)
    diagnostics._sessions.engine.playbooks = [Playbook(
        id="fixture", fault=fault, manufacturer="Fixture OEM", model="fixture-model", revision="R1",
        approved_by="test-only", approval_reference="synthetic fixture", source=source,
        hypothesis="Synthetic hypothesis only.", evidence_request=dict(
            request_id="fixture-request", type="technician_report", target="fixture display",
            instruction="Describe fixture display.", reason="Synthetic test.",
            source_references=[source], safety_status="ALLOWED_ADVISORY"),
    )]
    response = create(client, catalog, PILOT_FAULTS[fault][0])
    assert response.status_code == 201
    assert response.json()["assessment"]["status"] == "NEED_EVIDENCE"
    observed = client.post("/api/v1/diagnostic-sessions/session/observations", json=dict(
        observation_id="report-1", type="technician_report", parameter="fixture display",
        value="fixture text", source="operator",
    ))
    assert observed.status_code == 200
    assert observed.json()["assessment"]["status"] == "ESCALATE"
    assert observed.json()["assessment"]["next_evidence_request"] is None


def test_claimed_verification_and_mismatched_assets_rejected(api):
    client, _, catalog = api
    create(client, catalog)
    assert client.post("/api/v1/diagnostic-sessions/session/observations", json=dict(
        observation_id="bad", type="visual", parameter="display", value="text", source="operator",
        verification_status="verified",
    )).status_code == 422
    asset = catalog.require("assets", "asset").asset.model_dump(mode="json")
    asset["model"] = "wrong"
    assert client.post("/api/v1/diagnostic-sessions", json=dict(
        session_id="wrong", asset=asset, reported_problem="fails to start",
    )).status_code == 422
