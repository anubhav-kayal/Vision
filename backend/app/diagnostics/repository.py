"""Persistence boundary for diagnostic sessions.

The in-memory implementation is deliberately small. A database-backed repository can
replace it later without changing the application service or diagnostic engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.diagnostics.models import DiagnosticSession


class DiagnosticSessionRepository(ABC):
    @abstractmethod
    def save(self, session: DiagnosticSession) -> DiagnosticSession:
        raise NotImplementedError

    @abstractmethod
    def get(self, session_id: str) -> DiagnosticSession | None:
        raise NotImplementedError

    def save_assessment(self, session, assessment):
        return self.save(session)

    def history(self, session_id):
        return []


class InMemoryDiagnosticSessionRepository(DiagnosticSessionRepository):
    def __init__(self) -> None:
        self._sessions: dict[str, DiagnosticSession] = {}
        self._history = {}

    def save_assessment(self, session, assessment):
        self._history.setdefault(session.session_id, []).append(assessment.model_copy(deep=True))
        return self.save(session)

    def history(self, session_id):
        return [item.model_copy(deep=True) for item in self._history.get(session_id, [])]

    def save(self, session: DiagnosticSession) -> DiagnosticSession:
        self._sessions[session.session_id] = session.model_copy(deep=True)
        return session.model_copy(deep=True)

    def get(self, session_id: str) -> DiagnosticSession | None:
        session = self._sessions.get(session_id)
        return session.model_copy(deep=True) if session else None
