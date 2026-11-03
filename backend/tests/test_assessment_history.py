from backend.app.diagnostics.application import DiagnosticApplicationService
from backend.app.persistence import Base, database
from backend.app.sql_repositories import SqlDiagnosticSessionRepository
from backend.tests.test_diagnostic_application import make_asset
from backend.tests.test_diagnostic_engine import make_engine


def test_sql_history_persists_complete_retrieval_log(tmp_path):
    engine, sessions = database(f"sqlite:///{tmp_path / 'history.db'}")
    Base.metadata.create_all(engine)
    repository = SqlDiagnosticSessionRepository(sessions)
    service = DiagnosticApplicationService(make_engine(), repository)
    _, assessment = service.create_session(
        session_id="history", asset=make_asset(), reported_problem="high temperature",
    )
    history = SqlDiagnosticSessionRepository(sessions).history("history")
    assert history == [assessment]
    assert history[0].retrieval.retrieved_chunk_ids
    assert history[0].sources
