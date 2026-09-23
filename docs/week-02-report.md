# Week 2 Failure Analysis and Architecture Review

## 1. Objective

We tested whether an asset-aware, evidence-first diagnostic loop can maintain qualitative hypotheses and request a useful next observation without jumping directly from symptom to repair.

## 2. What we built

- Asset context and wrong-machine retrieval filtering.
- Structured symptoms, observations, hypotheses, evidence requests, and diagnostic states.
- A deterministic Diagnostic Engine V0 for compressor temperature symptoms.
- Multi-turn sessions with preserved observations, corrections, request history, and provenance.
- Transparent next-best-evidence ranking with conservative safety placeholders.
- A 15-case deterministic diagnostic evaluation suite.

## 3. Current data flow

Asset + problem + observations → diagnostic query → asset-filtered TF-IDF retrieval → source-backed hypotheses → evidence candidates → deterministic safety/duplicate filtering → selected next observation → updated session.

Authoritative documentation, technician observations, and AI hypotheses remain separate structures.

## 4. Week 1 regression results

The Week 1 evaluator still runs successfully. Its baseline remains unchanged: fixed-size retrieval hit rate 80.0%, section-aware retrieval hit rate 80.0%, and correct refusal 0.0%. The existing four failed cases remain visible; they were not hidden or reclassified.

## 5. Diagnostic evaluation results

The Week 2 suite contains 15 grounded cases spanning missing measurements, ambiguous symptoms, supported visual evidence, contradictory/clean observations, unknown faults, asset-family mismatch, manufacturer mismatch, and revision variation.

| Metric | Result |
|---|---:|
| Correct diagnostic status | 100.0% |
| Expected hypothesis coverage | 100.0% |
| Acceptable next-evidence rate | 100.0% |
| Unsupported action absence | 100.0% |
| Provenance presence | 100.0% |

These are deterministic V0 metrics on a small curated set, not evidence of production diagnostic accuracy.

## 6. Failed cases

No Week 2 diagnostic cases failed in the final run. The report intentionally retains the Week 1 failures because the Week 2 work does not change their evaluation semantics.

## 7. Failure taxonomy

The current Week 1 failures are primarily `RETRIEVAL_FAILURE` and `SAFETY_CLASSIFICATION_FAILURE`/insufficient refusal coverage. The diagnostic suite does not yet expose a production-scale `HYPOTHESIS_GENERATION_FAILURE`; its narrow scope is a limitation, not proof that the general problem is solved.

## 8. Most dangerous failure

The most dangerous failure is cross-machine contamination or an unsafe procedure being presented as ordinary guidance. The current design reduces known identity conflicts and blocks unknown/restricted evidence candidates, but the safety placeholder is not a production policy engine.

## 9. Most common failure

The most common observed Week 1 failure is missing or poorly ranked retrieval for safety and unsupported-knowledge cases. The diagnostic V0 intentionally refuses unsupported problem patterns rather than fabricating a diagnostic tree.

## 10. Architecture decisions

- Keep the modular monolith and reuse the Week 1 retrieval index.
- Use qualitative support levels instead of uncalibrated probabilities.
- Preserve observation corrections instead of overwriting history.
- Keep next-evidence selection deterministic and inspectable.
- Treat `REQUIRES_SUPERVISION`, `SAFETY_BLOCK`, and `UNKNOWN` as boundaries, not permissions.
- Keep model/provider integration deferred until the deterministic contracts and evaluation are stronger.

## 11. Technical debt

### Must fix soon

- Expand grounded diagnostic cases with technician/domain review.
- Improve retrieval for safety and refusal cases.
- Add explicit request-level safety policy enforcement and audit logging.
- Add semantic evaluation only where deterministic matching is insufficient.

### Can wait

- Dense embeddings and reranking.
- Persistent session storage.
- Multimodal image/audio processing.
- Mobile UI, live model integration, and repair execution workflows.

## 12. Domain questions for the founder/technicians

- Which observations are safe for a technician to collect without isolation or permit steps?
- Which temperature, pressure, vibration, and fault-code thresholds are asset-specific?
- Which procedures always require supervisor review or escalation?
- What constitutes verified completion after a diagnostic finding?

## 13. Recommended Week 3

Use technician-reviewed cases to strengthen refusal and safety evaluation, then test a provider-backed structured answer layer behind the existing provenance and deterministic safety boundaries. Do not add repair execution until those tests are credible.
