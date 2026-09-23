"""Deterministic evidence-first diagnostic engine V0."""

from __future__ import annotations

from backend.app.diagnostics.models import (
    DiagnosticAssessment,
    DiagnosticRetrievalLog,
    DiagnosticStatus,
    EvidenceCandidate,
    EvidenceRequest,
    EvidenceRequestType,
    Hypothesis,
    Observation,
    ObservationType,
    SafetyStatus,
    SupportLevel,
    Symptom,
)
from backend.app.models import AssetContext, GroundedSource
from ingestion.retrieval import RetrievedChunk, TfidfIndex


class DiagnosticEngineV0:
    """Use retrieved documentation to propose hypotheses, never repair actions."""

    def __init__(self, index: TfidfIndex, *, top_k: int = 8) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        self.index = index
        self.top_k = top_k

    def assess(
        self,
        asset: AssetContext,
        reported_problem: str,
        *,
        symptoms: list[Symptom] | None = None,
        observations: list[Observation] | None = None,
        previous_requests: list[EvidenceRequest] | None = None,
    ) -> DiagnosticAssessment:
        if not reported_problem.strip():
            raise ValueError("reported_problem must not be empty")
        symptoms = symptoms or []
        observations = observations or []
        previous_requests = previous_requests or []
        query = self._build_query(asset, reported_problem, symptoms, observations)
        retrieved = self.index.retrieve(query, top_k=self.top_k, asset_context=asset)
        retrieval_log = DiagnosticRetrievalLog(
            query=query,
            asset_filters=asset.model_dump(exclude_none=True),
            retrieved_chunk_ids=[result.chunk_id for result in retrieved],
            retrieved_scores={result.chunk_id: result.score for result in retrieved},
        )
        sources = [self._source(result) for result in retrieved]

        if not retrieved:
            return DiagnosticAssessment(
                status=DiagnosticStatus.INSUFFICIENT_KNOWLEDGE,
                summary="No applicable documentation was retrieved for this asset and problem.",
                sources=[],
                limitations=["The knowledge base does not support a meaningful assessment."],
                retrieval=retrieval_log,
            )

        problem_text = " ".join(
            [reported_problem, *(symptom.description for symptom in symptoms)]
        ).casefold()
        evidence_text = " ".join(result.text for result in retrieved).casefold()
        if not any(term in problem_text for term in ("temperature", "overheat", "hot")):
            return DiagnosticAssessment(
                status=DiagnosticStatus.INSUFFICIENT_KNOWLEDGE,
                summary="The V0 engine has no deterministic hypothesis pattern for this problem.",
                sources=sources,
                limitations=["Diagnostic Engine V0 only handles compressor temperature symptoms."],
                retrieval=retrieval_log,
            )

        hypotheses = self._temperature_hypotheses(observations, retrieved, evidence_text)
        if not hypotheses:
            return DiagnosticAssessment(
                status=DiagnosticStatus.INSUFFICIENT_KNOWLEDGE,
                summary="Retrieved documentation does not support a meaningful temperature hypothesis.",
                sources=sources,
                limitations=["No source-backed V0 hypothesis matched the retrieved evidence."],
                retrieval=retrieval_log,
            )

        temperature_observations = [
            observation
            for observation in observations
            if observation.parameter.casefold() in {"temperature", "discharge_temperature"}
            or observation.type is ObservationType.MEASUREMENT
            and "temp" in observation.parameter.casefold()
        ]
        if not temperature_observations:
            request = EvidenceRequest(
                request_id="REQ-TEMP-001",
                type=EvidenceRequestType.MEASUREMENT,
                target="compressor discharge temperature",
                instruction="Record the compressor discharge temperature and its unit.",
                reason="A verified temperature measurement is needed before distinguishing possible causes.",
                related_hypotheses=[hypothesis.hypothesis_id for hypothesis in hypotheses],
                source_references=[self._source(result) for result in retrieved[:2]],
                safety_status=SafetyStatus.ALLOWED_ADVISORY,
            )
            candidates = [
                self._candidate(
                    request,
                    hypotheses,
                    observations,
                    previous_requests,
                    supported=True,
                )
            ]
        else:
            cooling_request = EvidenceRequest(
                request_id="REQ-COOLING-001",
                type=EvidenceRequestType.VISUAL,
                target="compressor cooling surfaces",
                instruction="Visually inspect compressor cooling surfaces for dirt or blockage.",
                reason="This observation tests whether cooling-surface fouling contributes to the high temperature.",
                related_hypotheses=["HYP-COOLING-001"],
                source_references=[self._source(result) for result in retrieved[:3]],
                safety_status=SafetyStatus.REQUIRES_SUPERVISION,
            )
            filter_request = EvidenceRequest(
                request_id="REQ-AIRFLOW-001",
                type=EvidenceRequestType.VISUAL,
                target="compressor air intake filter",
                instruction="Visually inspect the compressor air intake filter for dirt or blockage.",
                reason="This observation tests whether intake restriction contributes to the high temperature.",
                related_hypotheses=["HYP-AIRFLOW-001"],
                source_references=[self._source(result) for result in retrieved[:3]],
                safety_status=SafetyStatus.REQUIRES_SUPERVISION,
            )
            candidates = [
                self._candidate(
                    cooling_request,
                    hypotheses,
                    observations,
                    previous_requests,
                    supported=True,
                ),
                self._candidate(
                    filter_request,
                    hypotheses,
                    observations,
                    previous_requests,
                    supported=True,
                ),
            ]
        visual_observations = [
            observation
            for observation in observations
            if observation.type is ObservationType.VISUAL
            and any(term in str(observation.value).casefold() for term in ("dirty", "blocked", "restricted"))
        ]
        assessment_status = (
            DiagnosticStatus.DIAGNOSIS_SUPPORTED
            if visual_observations
            else DiagnosticStatus.NEED_EVIDENCE
        )
        from backend.app.diagnostics.evidence_selection import select_next_evidence

        selected = select_next_evidence(candidates)
        return DiagnosticAssessment(
            status=assessment_status,
            summary="The evidence supports multiple possible temperature-related causes; it does not distinguish them yet.",
            hypotheses=hypotheses,
            next_evidence_request=None if visual_observations or selected is None else selected.request,
            sources=sources,
            limitations=["This V0 assessment does not recommend component replacement or repair execution."],
            retrieval=retrieval_log,
            evidence_candidates=candidates,
        )

    @staticmethod
    def _candidate(request, hypotheses, observations, previous_requests, *, supported):
        from backend.app.diagnostics.evidence_selection import rank_candidate

        return rank_candidate(
            request,
            supported_by_documentation=supported,
            discriminates_hypotheses=request.related_hypotheses,
            observations=observations,
            previous_requests=previous_requests,
        )

    @staticmethod
    def _build_query(
        asset: AssetContext,
        problem: str,
        symptoms: list[Symptom],
        observations: list[Observation],
    ) -> str:
        values = [
            asset.manufacturer or "",
            asset.equipment_family or "",
            asset.model or "",
            asset.revision or "",
            problem,
            *(symptom.description for symptom in symptoms),
            *(f"{observation.parameter} {observation.value}" for observation in observations),
            "compressor temperature cooling surfaces air intake filter lubricant cooler maintenance",
        ]
        return " ".join(value for value in values if value).strip()

    @staticmethod
    def _temperature_hypotheses(
        observations: list[Observation], retrieved: list[RetrievedChunk], evidence_text: str
    ) -> list[Hypothesis]:
        observation_ids = [observation.observation_id for observation in observations]
        sources = [
            DiagnosticEngineV0._source(result)
            for result in retrieved
            if any(term in result.text.casefold() for term in ("cooling", "filter", "lubricant"))
        ][:3]
        hypotheses: list[Hypothesis] = []
        clean_observations = [
            observation
            for observation in observations
            if observation.type is ObservationType.VISUAL
            and any(term in str(observation.value).casefold() for term in ("clean", "normal", "clear"))
        ]
        dirty_observations = [
            observation
            for observation in observations
            if observation.type is ObservationType.VISUAL
            and any(term in str(observation.value).casefold() for term in ("dirty", "blocked", "restricted"))
        ]
        if "cool" in evidence_text or "temperature" in evidence_text:
            hypotheses.append(
                Hypothesis(
                    hypothesis_id="HYP-COOLING-001",
                    description="Restricted or fouled cooling surfaces may be contributing to the high temperature.",
                    status=(
                        "supported" if dirty_observations else "contradicted" if clean_observations else "active"
                    ),
                    supporting_evidence=observation_ids if not clean_observations else [],
                    contradicting_evidence=[item.observation_id for item in clean_observations],
                    support_level=(
                        SupportLevel.SUPPORTED
                        if dirty_observations
                        else SupportLevel.UNKNOWN
                        if clean_observations
                        else SupportLevel.WEAKLY_SUPPORTED
                    ),
                    source_references=sources,
                )
            )
        if "filter" in evidence_text or "air intake" in evidence_text:
            hypotheses.append(
                Hypothesis(
                    hypothesis_id="HYP-AIRFLOW-001",
                    description="Restricted air intake or filter condition may be contributing to the high temperature.",
                    status=(
                        "supported" if dirty_observations else "contradicted" if clean_observations else "active"
                    ),
                    supporting_evidence=observation_ids if not clean_observations else [],
                    contradicting_evidence=[item.observation_id for item in clean_observations],
                    support_level=(
                        SupportLevel.SUPPORTED
                        if dirty_observations
                        else SupportLevel.UNKNOWN
                        if clean_observations
                        else SupportLevel.WEAKLY_SUPPORTED
                    ),
                    source_references=sources,
                )
            )
        return hypotheses

    @staticmethod
    def _source(result: RetrievedChunk) -> GroundedSource:
        return GroundedSource(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            page=result.printed_page or result.page,
            section=result.section,
            supporting_text=result.text,
        )
