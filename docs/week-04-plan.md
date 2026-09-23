# Week 4 Plan - Versioned Diagnostic HTTP API

## Objective

Expose the Week 3 application service through a thin, versioned HTTP boundary that future clients can use without coupling to domain internals.

## Scope

- Health endpoint.
- Create, retrieve, and add-observation diagnostic-session endpoints.
- RFC 9457-style Problem Details for missing sessions and validation failures.
- Dependency injection so the API can use in-memory or persistent repositories.
- Contract tests for the complete HTTP workflow.

## Safety boundary

The API stores diagnostic state and returns advisory assessments only. It has no endpoint for repair execution, machine control, PLC/SCADA writes, or actuator commands.

## Definition of done

A client can create a session, retrieve it, submit an observation, and receive a reassessment. Invalid requests and missing sessions return structured problem responses, and the full regression suite remains green.
