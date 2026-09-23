# Week 3 Plan - Application Boundary and Operational Readiness

## Objective

Turn the Week 2 diagnostic domain into a stable application boundary that a future API, mobile client, or batch evaluator can call without depending on engine internals.

## Scope

- Add a repository interface with an in-memory implementation.
- Add an application service for create, retrieve, add-observation, and reassess flows.
- Preserve the evidence-first and read-only safety posture.
- Keep persistence, authentication, mobile UI, and machine control deferred.
- Add integration tests and a Week 3 report.

## Definition of done

A caller can create a diagnostic session, receive its first assessment, add an observation, receive a reassessment, and retrieve the stored session through a stable service boundary. Repository state is isolated from caller mutation, unknown sessions fail explicitly, and the complete Week 1/Week 2 regression suite remains green.
