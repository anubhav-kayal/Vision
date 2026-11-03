# Two-week implementation report

## Result

The backend implementation now covers the ten-day plan as an executable local
pilot. External acceptance remains open: an authorized generator manual, actual
asset configuration, domain-approved playbooks, and live model credentials are
not available. Consequently this is not an accepted factory deployment or a
validated generator repair system.

## Plan coverage

| Day | Implementation | Verification / remaining acceptance |
| --- | --- | --- |
| 1 | Component identity, status and image/draft contracts | Model validation tested; existing enum values preserved |
| 2 | SQL/memory catalog repositories; sites, organizations, assets, revisions and sessions | Contract, ownership, update and restart tests |
| 3 | PDF ingestion service and immutable revision registration | Real generated PDF upload tested; page/provenance and rejection tests |
| 4 | TF-IDF baseline, hybrid fusion, PostgreSQL full text and optional pgvector | Live PostgreSQL/vector test passed; hosted embedding benchmark pending |
| 5 | Exact applicable corpus, refusal threshold, wrong-identity and retirement checks | Synthetic/contract cases pass; domain retrieval set pending |
| 6 | Provider interfaces and Responses text/vision/embedding adapters | Offline schema/refusal/timeout tests; live quality/availability pending |
| 7 | Bounded image intake, content validation/hash, storage, vision draft and confirmation | Real image bytes tested; clarity, refusal, mismatch and ownership tests |
| 8 | Five generator fault routes and source-gated playbook framework | Synthetic paths tested; real approved diagnostic content pending |
| 9 | Authenticated pilot HTTP workflow, technician projection and history | End-to-end tests across memory/SQL catalogs |
| 10 | Regression script, pilot evaluation, runtime factory and operating runbook | Software checks pass; factory/operator acceptance pending |

## Working flow

Register organization/site/asset → register and ingest manual → create diagnostic
session → retrieve applicable sources → select an approved playbook → optionally
check model proposals → return an allowed evidence request or escalate → upload
image → confirm a technician observation → reassess → preserve complete history.

No manual means `INSUFFICIENT_KNOWLEDGE`. A matching document without an approved
playbook means `ESCALATE`. Unknown/supervised/blocked evidence requests are withheld
from ordinary guidance. Empty or ungrounded model proposals fail conservatively.
Vision drafts never create observations automatically; confirmation records a
technician report rather than a verified measurement.

The optional model checks only approved hypotheses and supplied source/evidence
identifiers. Citation validation does not prove semantic entailment. Playbook
approval fields record an assertion, not authenticated domain certification.

## Actual checks

- Complete configured run: **142 passed**, including the live PostgreSQL/pgvector test.
- Latest run after history-ordering fix: **141 passed, 1 skipped**; the opt-in
  database test was skipped after its disposable container was removed.
- Python compilation: passed for backend, ingestion, evaluation and migrations.
- Whitespace validation: passed.
- Migration upgrade → downgrade → upgrade: passed on SQLite.
- PostgreSQL migrations, full-text ranking, vector indexing/search, model/site
  exclusion: passed in a local RAM-backed PostgreSQL 17 container.
- Narrow correctness lint for new runtime/retrieval modules: passed. A broad Ruff
  run also reported style issues; repository-wide style cleanup is not claimed.
- Five PyMuPDF SWIG deprecation warnings remain in the test output.

Evaluation results:

| Evaluation | Actual result | Interpretation |
| --- | --- | --- |
| Historical Week 1, 12 cases | 80% retrieval hit; 0% correct refusal; four failures retained | Existing baseline remains unresolved |
| Historical Week 2, 15 cases | All five deterministic metrics 100%; zero failed cases | Narrow curated compressor evaluation only |
| New pilot workflow, 15 cases | All expected statuses; no unsafe requests; zero failed cases | Synthetic software behavior, not industrial accuracy |

Pilot results include per-case latency. Live model latency/cost, actual fault
accuracy, OCR performance, real refusal quality, and business impact are unmeasured.
No external model calls were made because no API credential was configured.

## SSD compatibility issue resolved for local operation

Direct SQLite files on this SSD failed with `SQLITE_READONLY_DBMOVED`; PostgreSQL
initialization failed because of AppleDouble sidecars. An APFS sparse image was
created at `.runtime/pilot-data.sparseimage` on the SSD. It is currently mounted at
`/Volumes/VisionPilotData`. Test/database files inside that virtual volume remain
physically backed by the external SSD. Nothing reformatted the physical SSD.

Use the APFS image or an appropriate PostgreSQL host. The regression script accepts
`VISION_TEST_TMP`. The runbook explains mounting/configuration after reboot.
Both disposable test containers were stopped and removed; only synthetic test
data was discarded. The downloaded container image remains cached. The APFS
image and its test artifacts remain available on the SSD and are ignored by Git.

## Remaining release gates

1. Obtain the authorized GPWII-35 manual and confirm engine, alternator, controller,
   serial range, and revision applicability. No manufacturer facts were invented.
2. Have a qualified reviewer approve diagnostic hypotheses, safe evidence requests,
   source excerpts, stopping rules, and escalation boundaries for each fault.
3. Configure a permitted hosted API credential and assess text/vision output,
   latency, cost, retention, and model availability on representative evidence.
4. Compare embedding models and tune retrieval thresholds against domain-reviewed
   cases; current hybrid fusion requires lexical eligibility.
5. Resolve conflicting source authority and revised bulletin policy with the domain
   reviewer. Current filtering is not a complete conflict-resolution engine.
6. Conduct supervised operator acceptance. The shared token and process-local
   locks are limited to this single-worker pilot; production tenant isolation,
   identity roles, distributed concurrency, backups and monitoring remain deferred.

Approved repair execution, verified resolution/service outcomes, mobile UI and
historical learning were outside this ten-day backend slice and remain pending.
Safety placeholders have not become a production safety policy engine.

## Navigation

- Operating instructions: [pilot-runbook.md](pilot-runbook.md).
- Implementation schedule: [two-week-implementation-plan.md](two-week-implementation-plan.md).
- Regression entry point: `sh scripts/check.sh` with the runbook environment.
- Implementation commits start at `60f9424`; the last code fix is `60134da`.
- Every implementation commit is below 200 changed lines. No changes were pushed.
