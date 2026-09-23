# Week 3 Report - Application Boundary and Operational Readiness

## Objective

Week 3 tested whether the Week 2 diagnostic engine could be exposed through a stable application workflow without coupling callers to retrieval or engine internals.

## What was built

- `DiagnosticSessionRepository` interface.
- In-memory repository implementation with defensive copies.
- `DiagnosticApplicationService` for session creation, retrieval, observation intake, and reassessment.
- Integration tests for the complete create → assess → observe → reassess loop.
- Explicit missing-session errors.
- Week 3 plan and this report.

## Data flow

Caller → application service → repository/domain session → diagnostic session service → engine → assessment → repository.

The application service remains read-only with respect to physical equipment. It stores diagnostic state only; it does not execute repairs or communicate with PLC, SCADA, motors, valves, or safety systems.

## Verification

- 37 tests passed.
- Python compilation passed.
- Diff validation passed.
- Week 1 and Week 2 behavior remains covered by the full regression suite.

## Decisions

- Use a repository interface before introducing a database.
- Return defensive copies so callers cannot mutate stored state without going through the service.
- Keep `KeyError` for a missing session at this internal boundary; an HTTP adapter can translate it to a 404 later.
- Keep API framework, authentication, persistence, and deployment separate from the diagnostic domain.

## Deferred work

- FastAPI or another HTTP adapter.
- Database-backed persistence and migrations.
- Authentication and authorization.
- Background jobs and notifications.
- Production safety policy enforcement.
- Machine-control integration.

## Recommended next step

Add a thin HTTP adapter with RFC 9457-compatible errors only after the service contract receives domain review. Then add a small persistent repository and contract tests that run against both the in-memory and database implementations.
