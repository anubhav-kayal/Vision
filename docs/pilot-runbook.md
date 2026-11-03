# Local pilot runbook

## Setup

Run from the external SSD checkout with Python 3.12 or newer:

```bash
cd '/Volumes/Anubhav SSD/Vision'
source .venv/bin/activate
python -m pip install -e '.[dev]'
mkdir -p .runtime
export VISION_DATABASE_URL='sqlite:///.runtime/pilot.db'
export VISION_DATA_DIR='.runtime'
export VISION_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -m alembic upgrade head
python -m uvicorn backend.app.runtime:create_runtime --factory --host 127.0.0.1 --port 8000
```

Preserve the token securely for client requests. Use one worker: the pilot uses
process-local locks and has no distributed concurrency/authorization policy.
SQLite is the runnable local default. It is not the PostgreSQL retrieval benchmark.

Open `http://127.0.0.1:8000/docs`, select Authorize, and enter the token. The schema
and health endpoints are public; data endpoints require the bearer token.

## Workflow

1. `POST /api/v1/organizations`: register an ID and name.
2. `POST /api/v1/sites`: register an ID, organization ID, and name.
3. `POST /api/v1/assets`: provide a site ID and the full asset object.
4. `POST /api/v1/documents`: register an immutable document revision ID, site,
   asset, and `KnowledgeDocument` manifest.
5. `PUT /api/v1/documents/{revision_id}/content`: upload PDF bytes with
   `Content-Type: application/pdf` (20 MiB maximum).
6. `POST /api/v1/diagnostic-sessions`: send a unique session ID, the exact
   registered asset, and the reported problem.
7. `POST /api/v1/diagnostic-sessions/{id}/images`: upload raw JPEG, PNG, or WebP
   bytes (8 MiB maximum). Optional `X-Technician-ID` identifies the operator.
8. `POST /api/v1/diagnostic-sessions/{id}/images/{evidence_id}/confirmation`:
   send `description`, `parameter`, and `confirmed_by`.
9. Inspect returned status, next evidence, sources, and escalation reason.
10. `GET /api/v1/diagnostic-sessions/{id}/history` returns complete assessments.

Updates use `PUT /api/v1/assets/{id}`. Retire a ready document using
`POST /api/v1/documents/{revision_id}/supersession`; retired content is excluded.
Historical assessments retain their original citations after retirement.

The exact registered manufacturer, family, model, and revision must match the
document applicability record. Obtain the actual GPWII-35 configuration and an
authorized manual before entering real machine facts. Do not guess identifiers.
Document revision versus equipment configuration mapping needs domain review.

## Approved playbooks

Set `VISION_PLAYBOOKS` to an authorized JSON array matching
`backend.app.diagnostics.playbooks.Playbook`. Its fields are:

```text
id, fault, manufacturer, model, revision, approved_by, approval_reference,
source, hypothesis, evidence_request
```

`fault` must identify one of the five keys in `PILOT_FAULTS`. Source excerpts must
match retrieved chunk ID, document ID, page, section, and text. Requests must
include their own source references. Missing/ambiguous approval or source evidence
causes refusal or escalation. A nonempty approval field records an assertion;
this pilot does not authenticate an approver or verify their qualifications.

No real generator playbook is bundled as approved guidance. Synthetic evaluation
fixtures demonstrate the software contract only. With no approved playbook, a
matching manual can be retrieved but the investigation escalates.

## Optional hosted models

Export `OPENAI_API_KEY` through your secure environment, then:

```bash
export VISION_ENABLE_MODELS=1
export VISION_MODEL=gpt-6.1-sol
```

Restart the API. SDK calls use a 30-second timeout, one retry, and `store=False`.
Images are sent only when the hosted adapter is enabled. Obtain approval before
sending factory evidence to an external provider. Never commit credentials.
Model access and output quality require live account validation.

The model supplies validated proposals; approved playbook text remains the source
of displayed hypotheses and evidence requests. No automatic stronger-model retry
is enabled: ambiguous cases escalate to a human review boundary.

## PostgreSQL and pgvector

Point `VISION_DATABASE_URL` to a dedicated PostgreSQL database, then run:

```bash
export VISION_RETRIEVAL=postgres
export VISION_ENABLE_VECTOR=1
python -m alembic upgrade head
# For an existing database originally migrated without vector storage:
python -m ingestion.postgres
```

Vector indexing additionally needs hosted models enabled and a valid embedding
credential. Without vectors, PostgreSQL full-text search remains available.
Ingestion populates the search tables. Existing ready documents need an explicit
administrative call to `index_document`; they are not automatically reindexed.
Fusion uses lexical eligibility plus vector ranking and preserves citations.
Semantic-only matches are deliberately excluded pending domain evaluation.

Do not place native PostgreSQL data files directly on this SSD filesystem: an
attempt failed due to AppleDouble sidecars during initialization. Use a compatible
PostgreSQL host. Integration tests were run in an ephemeral RAM-backed container.

## Checks

```bash
sh scripts/check.sh
```

To opt into the database integration test, export `VISION_TEST_DATABASE_URL` for a
dedicated disposable database. This test runs migrations and inserts synthetic
records; never point it at a production database.

The script removes only identified generated AppleDouble Python sidecars and runs
tests, all three evaluations, compilation, and whitespace validation. Week 1 still
has four known retrieval failures; a successful runner exit is not a perfect score.

This is a local advisory backend pilot. There is no technician mobile UI, repair
execution, verified-resolution workflow, calibrated confidence, tenant isolation,
role-based access, production safety engine, or production deployment in this slice.
