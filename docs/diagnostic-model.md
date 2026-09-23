# Week 2 Diagnostic Model

## Purpose

These are domain contracts for an evidence-first diagnostic investigation. They do not implement diagnosis, prescribe repairs, or control equipment.

## Symptom vs observation

A `Symptom` is what a technician reports, such as “machine overheating.” It is not automatically a verified measurement and can carry an optional qualitative confidence.

An `Observation` is evidence collected during the investigation. It records a type, parameter, value, unit where applicable, source, verification status, and timestamp. Measurements must have numeric values and units; fault codes require strings; visual/audio observations require a text description or reference.

## Hypothesis

A `Hypothesis` is a possible explanation, not a conclusion. It records supporting and contradicting observation IDs, a qualitative support level, a lifecycle status, and optional grounded source references. V0 deliberately does not use arbitrary numeric probabilities such as `0.83`; those numbers would imply calibration that does not yet exist.

## Evidence request

An `EvidenceRequest` states what evidence to collect, how to collect it at a high level, why it matters, which hypotheses it tests, and its safety status. A request marked `SAFETY_BLOCK`, `REQUIRES_SUPERVISION`, or `UNKNOWN` must not be treated as a normal technician instruction by future engines.

## Diagnostic state

`DiagnosticSession.status` uses explicit states:

- `NEED_EVIDENCE`: current evidence is not sufficient to support a diagnosis.
- `DIAGNOSIS_SUPPORTED`: evidence supports a conclusion; this does not authorize repair execution.
- `INSUFFICIENT_KNOWLEDGE`: the knowledge base cannot support a reliable assessment.
- `SAFETY_BLOCK`: a proposed step crosses a safety boundary.
- `ESCALATE`: a qualified human or approved process is required.

There is intentionally no `SUCCESS` status because a successful outcome requires verification and is outside this model stage.

## Session validation

Sessions reject duplicate IDs, hypotheses that reference unknown observations, evidence requests that reference unknown hypotheses, and timestamps that move backward. This keeps multi-turn updates structurally coherent before an engine is introduced.
