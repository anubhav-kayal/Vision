# Architecture

## Initial boundary

The repository is a Python modular monolith. Day 1 contains only domain contracts and documentation. Later stages will add ingestion, retrieval, and grounded generation as replaceable modules rather than coupling them to a provider or API framework.

```text
source manual
    ↓
ingestion: parse → preserve pages → identify sections → chunk → attach metadata
    ↓
retrieval: lexical/vector baseline → ranked chunks with provenance
    ↓
answering: provider interface → structured grounded response
    ↓
evaluation: fixed cases → deterministic metrics → preserved report
```

## Domain contracts

`backend/app/models.py` contains the minimum shared vocabulary:

- `Asset`: identifies the physical asset and configuration.
- `AssetContext`: carries asset identity into retrieval and future diagnostic reasoning.
- `DiagnosticSession`: carries reported symptoms, observations, qualitative hypotheses, evidence requests, and explicit diagnostic status.
- `KnowledgeDocument`: records machine/document identity, revision, source, and authority.
- `ServiceCase`: captures symptoms, observations, and eventual verified outcome fields.
- `GroundedSource` and `GroundedAnswer`: define the provenance-bearing response boundary for later retrieval/LLM work.

The authority level is an enum today so invalid values fail early, while the ordering/policy decision is intentionally deferred. The model can represent the planned hierarchy without pretending that the policy engine already exists.

## Replacement boundaries

- A retrieval interface should return chunks plus scores and provenance; storage may start local and later move to PostgreSQL/pgvector.
- Retrieval accepts optional `AssetContext` and rejects known manufacturer, family, model, and revision conflicts while allowing generic family guidance.
- `backend.app.grounded_answering.ModelProvider` accepts a bounded context and returns JSON that is validated into `GroundedAnswer`; provider-specific SDK code remains outside this boundary.
- Evaluation must record configuration and distinguish deterministic metrics from model-graded metrics.

The ingestion boundary is `ingestion.pdf_parser.parse_pdf`, with page-preserving
text and replaceable chunking strategies. `TfidfIndex` remains the deterministic
retrieval baseline. The FastAPI adapter calls application services; Pydantic defines
the domain contracts and pytest verifies their behavior.

## Safety posture

The system is advisory and read-only. It must not control PLCs, valves, motors, or other physical systems. Future workflow states such as `NEED_EVIDENCE`, `SAFETY_BLOCK`, and `ESCALATE` should be explicit rather than inferred from a free-form answer.

## Known technical debt

- The current sample is a government technical sourcebook rather than an OEM model-specific service manual; model-specific authority and asset matching remain a later experiment.
- The pilot restricts applicable sources by authority but has no complete policy for
  resolving contradictory OEM bulletins, safety instructions, and internal SOPs.
- Retrieval, embedding, text, and vision provider boundaries are implemented. Live
  model quality and machine-specific facts still need external validation.
- TF-IDF remains the historical baseline. The pilot adds exact asset/revision
  filtering, optional PostgreSQL full-text/pgvector retrieval, and reciprocal-rank
  fusion. A learned reranker has not been evaluated.
- Grounded answer validation rejects malformed output and citations that do not match retrieved chunks; it does not yet verify every natural-language claim automatically.
- Diagnostic models are separated from the reasoning service; repair execution is not implemented.
- `backend.app.diagnostics.engine.DiagnosticEngineV0` provides a narrow deterministic temperature-assessment path that reuses retrieval and returns hypotheses/evidence requests without repair execution.
- `backend.app.diagnostics.session.DiagnosticSessionService` orchestrates multi-turn assessment while preserving observation history and request provenance.
- `backend.app.diagnostics.evidence_selection` ranks next-best evidence transparently and excludes stale, repeated, unavailable, or unsafe requests.
- `backend.app.diagnostics.application.DiagnosticApplicationService` is the caller-facing boundary for session creation, observation intake, reassessment, and retrieval; repository storage remains replaceable.
- `backend.app.api.create_app` exposes that application boundary through versioned HTTP routes and Problem Details errors; it has no machine-control endpoint.
- Evaluation cases are manually curated in `evaluation/cases/` and must not introduce facts absent from the selected source document.
- Dates and document source validation will need tighter rules once real inputs arrive.

## Local pilot composition

`runtime.create_runtime` wires SQL repositories, the catalog service, applicable
corpus, playbook engine, object storage, and authenticated pilot routes. SQLite is
the local default; PostgreSQL is optional. Alembic migrations are explicit.
Full assessment payloads are appended transactionally with session updates.
Image drafts remain unverified until confirmation; confirmation records a technician
report, not a verified measurement. No real OEM playbook is bundled as approved.

Use one API worker. Process-local locks are not distributed concurrency control.
The shared pilot token is not tenant isolation or role-based authorization.
See `pilot-runbook.md` for configuration and operating limitations.
