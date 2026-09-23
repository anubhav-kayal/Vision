"""Versioned HTTP adapter for the diagnostic application service."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.app.diagnostics.application import DiagnosticApplicationService
from backend.app.diagnostics.models import DiagnosticAssessment, DiagnosticSession, Observation, Symptom
from backend.app.models import Asset


class ProblemDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = "about:blank"
    title: str
    status: int
    detail: str


class CreateDiagnosticSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    asset: Asset
    reported_problem: str = Field(min_length=1)
    symptoms: list[Symptom] = Field(default_factory=list)


class DiagnosticAssessmentResponse(BaseModel):
    session: DiagnosticSession
    assessment: DiagnosticAssessment


def _response(session: DiagnosticSession, assessment: DiagnosticAssessment) -> DiagnosticAssessmentResponse:
    return DiagnosticAssessmentResponse(session=session, assessment=assessment)


def create_app(service: DiagnosticApplicationService) -> FastAPI:
    """Build the API with an injected service for testability and deployment flexibility."""

    app = FastAPI(title="Physical AI Diagnostic API", version="0.1.0")

    @app.exception_handler(KeyError)
    async def handle_missing_session(_: Request, exc: KeyError) -> JSONResponse:
        body = ProblemDetail(
            type="https://physical-ai.invalid/problems/session-not-found",
            title="Diagnostic session not found",
            status=404,
            detail=str(exc).strip("'"),
        )
        return JSONResponse(status_code=404, content=body.model_dump(), media_type="application/problem+json")

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        body = ProblemDetail(
            type="https://physical-ai.invalid/problems/validation-error",
            title="Request validation failed",
            status=422,
            detail=str(exc.errors()),
        )
        return JSONResponse(status_code=422, content=body.model_dump(), media_type="application/problem+json")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "diagnostic-api"}

    @app.post("/api/v1/diagnostic-sessions", response_model=DiagnosticAssessmentResponse, status_code=201)
    async def create_session(payload: CreateDiagnosticSessionRequest) -> DiagnosticAssessmentResponse:
        session, assessment = service.create_session(
            session_id=payload.session_id,
            asset=payload.asset,
            reported_problem=payload.reported_problem,
            symptoms=payload.symptoms,
        )
        return _response(session, assessment)

    @app.get("/api/v1/diagnostic-sessions/{session_id}", response_model=DiagnosticSession)
    async def get_session(session_id: str) -> DiagnosticSession:
        return service.get_session(session_id)

    @app.post(
        "/api/v1/diagnostic-sessions/{session_id}/observations",
        response_model=DiagnosticAssessmentResponse,
    )
    async def add_observation(session_id: str, observation: Observation) -> DiagnosticAssessmentResponse:
        session, assessment = service.add_observation(session_id, observation)
        return _response(session, assessment)

    return app
