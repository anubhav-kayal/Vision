"""Application service boundary for diagnostic session workflows."""

from __future__ import annotations

from backend.app.diagnostics.engine import DiagnosticEngineV0
from backend.app.diagnostics.models import (
    DiagnosticAssessment,
    DiagnosticSession,
    Observation,
    Symptom,
)
from backend.app.diagnostics.repository import DiagnosticSessionRepository
from backend.app.diagnostics.session import DiagnosticSessionService
from backend.app.models import Asset


class DiagnosticApplicationService:
    """Coordinates storage and domain services without exposing engine internals."""

    def __init__(self, engine: DiagnosticEngineV0, repository: DiagnosticSessionRepository) -> None:
        self._sessions = DiagnosticSessionService(engine)
        self._repository = repository

    def create_session(
        self,
        *,
        session_id: str,
        asset: Asset,
        reported_problem: str,
        symptoms: list[Symptom] | None = None,
    ) -> tuple[DiagnosticSession, DiagnosticAssessment]:
        session = DiagnosticSession(
            session_id=session_id,
            asset=asset,
            reported_problem=reported_problem,
            symptoms=symptoms or [],
        )
        return self._assess_and_save(session)

    def get_session(self, session_id: str) -> DiagnosticSession:
        session = self._repository.get(session_id)
        if session is None:
            raise KeyError(f"diagnostic session not found: {session_id}")
        return session

    def add_observation(
        self, session_id: str, observation: Observation
    ) -> tuple[DiagnosticSession, DiagnosticAssessment]:
        session = self.get_session(session_id)
        return self._assess_and_save(session.add_observation(observation))

    def _assess_and_save(
        self, session: DiagnosticSession
    ) -> tuple[DiagnosticSession, DiagnosticAssessment]:
        updated, assessment = self._sessions.assess(session)
        return self._repository.save(updated), assessment
