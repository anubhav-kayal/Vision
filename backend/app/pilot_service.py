"""Pilot application wiring binds each investigation to the registered asset."""

from backend.app.corpus import ApplicableCorpus
from backend.app.diagnostics.application import DiagnosticApplicationService
from backend.app.diagnostics.models import VerificationStatus
from backend.app.diagnostics.playbooks import PlaybookEngine
from ingestion.hybrid import HybridIndex


class CatalogEngine:
    def __init__(self, catalog, playbooks, provider=None, channel_factory=None):
        self.catalog, self.playbooks, self.provider = catalog, playbooks, provider
        self.channel_factory = channel_factory

    def assess(self, asset, problem, **kwargs):
        lexical = ApplicableCorpus(self.catalog.repository, asset.asset_id)
        index = self.channel_factory(asset) if self.channel_factory else HybridIndex(lexical)
        return PlaybookEngine(index, self.playbooks, self.provider).assess(asset, problem, **kwargs)


class PilotDiagnostics(DiagnosticApplicationService):
    def __init__(self, catalog, repository, playbooks=(), provider=None, channel_factory=None):
        self.catalog = catalog
        super().__init__(CatalogEngine(catalog, playbooks, provider, channel_factory), repository)

    def create_session(self, *, session_id, asset, reported_problem, symptoms=None):
        if self._repository.get(session_id):
            raise ValueError("duplicate session identifier")
        registered = self.catalog.require("assets", asset.asset_id).asset
        if asset != registered:
            raise ValueError("asset must match registered identity")
        return super().create_session(session_id=session_id, asset=registered,
                                      reported_problem=reported_problem, symptoms=symptoms)

    def add_observation(self, session_id, observation):
        if observation.verification_status is VerificationStatus.VERIFIED:
            raise ValueError("verification requires a qualified review workflow")
        return super().add_observation(session_id, observation)


def technician_response(session, assessment):
    request = assessment.next_evidence_request
    return dict(
        session_id=session.session_id, status=assessment.status,
        asset_status=session.asset.asset_status,
        document_applicability="DOCUMENT_APPLICABLE" if assessment.sources else "UNCONFIRMED",
        summary=assessment.summary,
        possible_causes=[dict(description=h.description, support=h.support_level)
                         for h in assessment.hypotheses],
        next_evidence=request, sources=assessment.sources,
        escalation_reason=assessment.summary if assessment.status.value in {
            "ESCALATE", "SAFETY_BLOCK", "INSUFFICIENT_KNOWLEDGE"} else None,
        safety_boundary="Advisory only. Follow approved site procedures and qualified review.",
    )
