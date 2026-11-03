# Two-Week Implementation Plan

## Objective

Build the first usable Vision product slice for one registered Greaves Power /
Crompton Greaves generator asset. It must accept a reported problem and optional
image, retrieve applicable evidence, produce structured hypotheses, request safe
next evidence, and preserve provenance.

This extends the current FastAPI modular monolith. It does not add machine
control, automatic repair, a native mobile app, or production deployment.

## Pilot fixture

Use one exact, approved configuration. The development fixture is Greaves Power
GPWII-35, subject to an authorized manual and confirmed engine, alternator,
controller, model, and revision identifiers.

Initial fault scenarios:

1. Generator fails to start.
2. High coolant temperature alarm.
3. Low oil pressure alarm.
4. Low output voltage.
5. Excessive vibration or abnormal noise.

Until domain review, procedures remain advisory and low-risk. Escalate electrical
panel work, interlock bypasses, fuel-system disassembly, governor/AVR adjustment,
wiring changes, and component replacement.

## Fixed technical decisions

- Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy, PostgreSQL, and Alembic.
- Keep the modular monolith; do not create microservices.
- Keep TF-IDF as a regression baseline while adding hybrid retrieval.
- Use PostgreSQL full-text search plus pgvector.
- Start embeddings with `text-embedding-3-small`; benchmark `text-embedding-3-large`.
- Use provider-neutral interfaces. The initial hosted adapter may use `gpt-6.1-sol`
  for normal text/image assessment and `gpt-6-astra` for ambiguous cases.
- Require schema-constrained model output and validate it again with Pydantic.
- Model output is limited to observations, hypotheses, evidence requests, and
  explanations; it never authorizes physical work.

## Required status vocabulary

```text
Asset:       ASSET_CONFIRMED, ASSET_UNCONFIRMED, ASSET_MISMATCH,
             MODEL_UNKNOWN, REVISION_UNKNOWN
Evidence:    EVIDENCE_REPORTED, EVIDENCE_VERIFIED, EVIDENCE_UNVERIFIED,
             EVIDENCE_CORRECTED, EVIDENCE_SUPERSEDED
Diagnostic:  NEED_EVIDENCE, DIAGNOSIS_SUPPORTED, INSUFFICIENT_KNOWLEDGE,
             ESCALATE, SAFETY_BLOCK
Safety:      ALLOWED_ADVISORY, REQUIRES_SUPERVISION, SAFETY_BLOCK, UNKNOWN
Support:     UNKNOWN, WEAKLY_SUPPORTED, SUPPORTED, STRONGLY_SUPPORTED
```

## Week 1 — contracts, persistence, and knowledge

### Day 1 — domain contracts

- Add pilot identifiers and status enums to `Asset` and `AssetContext`.
- Add `ImageEvidence`, `ObservationSource`, and assessment request/response models.
- Preserve current model compatibility.

Done when new validation tests pass and the existing 39-test suite remains green.

### Day 2 — asset and document persistence

- Add SQLAlchemy models for organizations, sites, assets, documents, and revisions.
- Add repository interfaces and an in-memory implementation.
- Add Alembic configuration and the initial migration.

Done when assets and document revisions can be created and fetched through services,
with repository contract tests.

### Day 3 — ingestion service

- Add document upload metadata and processing states.
- Wrap the current parser/chunker in an application service.
- Preserve document, revision, page, section, chunk, and source provenance.
- Reject incomplete or ambiguous manifests.

Done when a supplied manual becomes `READY`, failures become `REJECTED`, and
ingestion tests verify page/provenance preservation.

### Day 4 — hybrid retrieval

- Add full-text retrieval and embedding-provider abstractions.
- Add pgvector schema behind a feature flag.
- Merge lexical/vector results deterministically.
- Keep TF-IDF as a regression strategy.

Done when retrieval preserves current provenance fields, filters asset/model/revision
before ranking, and records its strategy in diagnostic logs.

### Day 5 — retrieval evaluation and refusal

- Add cases for the five generator faults.
- Add wrong-model, wrong-revision, generic-document, and missing-document cases.
- Add thresholds, refusal reasons, authority checks, and revision-conflict tests.
- Run Week 1, Week 2, and pilot evaluations.

Done when wrong-model documents are excluded and every refusal has a machine-readable
reason and failed case ID.

## Week 2 — structured model, images, and workflow

### Day 6 — model adapter

- Add `TextModelProvider`, `VisionModelProvider`, and `EmbeddingProvider` protocols.
- Add the Responses API adapter behind configuration.
- Define the diagnostic assessment JSON schema.
- Validate provider output with Pydantic.
- Safely handle refusal, timeout, and malformed output.

Done when provider code is outside domain logic, free-form output cannot reach the
API, and deterministic test doubles cover model calls.

### Day 7 — image evidence

- Add an image upload route for diagnostic sessions.
- Store image metadata and content hash through an object-storage adapter.
- Send bounded asset context plus image to the vision adapter.
- Return a visual observation requiring technician confirmation.

Done when invalid/oversized files are rejected, images cannot become verified
automatically, and ambiguous images return `NEED_EVIDENCE`.

### Day 8 — generator playbooks

- Add playbook models for the five pilot faults.
- Add approved evidence candidates and safety statuses.
- Replace the hardcoded temperature-only path with playbook selection.
- Keep hypotheses and next-evidence selection inspectable.
- Require source references for every hypothesis and request.

Done when each fault has a documented evidence path and unsafe requests are never
selected as normal next evidence.

### Day 9 — API and technician response

- Add image and evidence routes to the versioned API.
- Add a concise technician-facing response projection.
- Add asset confirmation, document applicability, and escalation reason codes.
- Preserve the full assessment for audit and evaluation.

Done when HTTP supports create session → add image → confirm observation → reassess,
with status, next evidence, safety boundary, and sources.

### Day 10 — validation and handoff

- Add end-to-end tests for all five fault scenarios.
- Add unsafe-action, wrong-asset, conflicting-evidence, and model-refusal tests.
- Record latency, retrieval quality, refusal quality, and provenance metrics.
- Document limitations and the next pilot gate.

Required checks:

```bash
PYTHONPATH=. python -m pytest
PYTHONPATH=. python -m evaluation.run --top-k 5
PYTHONPATH=. python -m evaluation.diagnostic_run
python -m compileall -q backend ingestion evaluation
git diff --check
```

## Commit discipline

Use one logical conventional commit per completed slice and keep each commit near
or below 200 changed lines. Split contracts, persistence, ingestion, retrieval,
provider, images, playbooks, API, and tests into separate commits when necessary.

Suggested messages:

```text
feat: define pilot asset and evidence contracts
feat: add persistent asset and document repositories
feat: add document ingestion application service
feat: add hybrid retrieval boundary
test: add generator retrieval and refusal cases
feat: add structured diagnostic model adapter
feat: add image evidence intake
feat: add generator diagnostic playbooks
feat: expose evidence workflow through api
test: add end-to-end generator pilot coverage
```

Commit messages must describe only the product change. Do not include workspace,
agent, or tool names, and do not add co-author tags.

## Out of scope

PLC/SCADA/control integration, automatic repair execution, native mobile apps,
predictive maintenance, multi-industry support, custom model training, and any
claim that the system is production-safe.
