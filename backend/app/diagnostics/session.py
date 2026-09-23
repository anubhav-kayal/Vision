"""Stateful multi-turn orchestration for diagnostic assessments."""

from __future__ import annotations

from backend.app.diagnostics.engine import DiagnosticEngineV0
from backend.app.diagnostics.models import DiagnosticAssessment, DiagnosticSession, utc_now


class DiagnosticSessionService:
    """Apply assessments to a session while retaining an auditable history."""

    def __init__(self, engine: DiagnosticEngineV0) -> None:
        self.engine = engine

    def assess(self, session: DiagnosticSession) -> tuple[DiagnosticSession, DiagnosticAssessment]:
        assessment = self.engine.assess(
            self._asset_context(session),
            session.reported_problem,
            symptoms=session.symptoms,
            observations=session.active_observations(),
            previous_requests=session.evidence_requests,
        )
        merged = session.model_copy(deep=True)
        merged.hypotheses = self._merge_hypotheses(merged.hypotheses, assessment.hypotheses)
        merged.sources = self._merge_sources(merged.sources, assessment.sources)
        merged.status = assessment.status
        if assessment.next_evidence_request:
            before = len(merged.evidence_requests)
            merged = merged.record_evidence_request(assessment.next_evidence_request)
            if len(merged.evidence_requests) == before:
                assessment = assessment.model_copy(
                    update={
                        "next_evidence_request": None,
                        "limitations": [
                            *assessment.limitations,
                            "The proposed evidence request was already recorded in this session.",
                        ],
                    }
                )
        merged.updated_at = utc_now()
        return DiagnosticSession.model_validate(merged), assessment

    @staticmethod
    def _asset_context(session: DiagnosticSession):
        from backend.app.models import AssetContext

        return AssetContext.from_asset(session.asset)

    @staticmethod
    def _merge_hypotheses(existing, assessed):
        by_id = {hypothesis.hypothesis_id: hypothesis for hypothesis in existing}
        for hypothesis in assessed:
            by_id[hypothesis.hypothesis_id] = hypothesis
        return list(by_id.values())

    @staticmethod
    def _merge_sources(existing, assessed):
        by_id = {source.chunk_id or f"{source.document_id}:{source.page}": source for source in existing}
        for source in assessed:
            by_id[source.chunk_id or f"{source.document_id}:{source.page}"] = source
        return list(by_id.values())
