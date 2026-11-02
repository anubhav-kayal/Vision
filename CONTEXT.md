# Project Context

## Migration Notes

This document summarizes the project context available while migrating the ChatGPT Project to Codex CLI.

Information is based only on:

- The current conversation history.
- Project-related pasted instructions and terminal output available in this chat.
- Previously discussed repository structure and implementation results.

I cannot access other ChatGPT project chats that were not included in this conversation. I also cannot currently verify the repository filesystem from this environment because the previously used workspace path is unavailable. Repository details below are based on the project context already available in this conversation.

---

## 1. Project Purpose and Objectives

The project is an early technical prototype for an industrial AI system supporting skilled physical work, initially focused on industrial maintenance and field-service technicians.

The intended system should help a trained technician:

1. Identify the exact physical asset.
2. Describe a fault using text, voice, or images.
3. Retrieve machine-specific technical knowledge.
4. Maintain possible diagnostic hypotheses.
5. Determine what evidence should be collected next.
6. Guide the technician through approved procedures.
7. Stop or escalate when evidence is insufficient or a safety boundary is reached.
8. Verify the result.
9. Create a structured service record.
10. Learn from verified service outcomes.

The intended long-term workflow is:

```text
IDENTIFY ASSET
→ DESCRIBE PROBLEM
→ OBSERVE
→ FORM HYPOTHESES
→ REQUEST EVIDENCE
→ UPDATE HYPOTHESES
→ GUIDE
→ VERIFY
→ DOCUMENT
→ LEARN
```

The central technical hypothesis is that a useful industrial assistant can combine:

```text
General multimodal foundation models
+ machine-specific technical knowledge
+ asset identity
+ structured diagnostic reasoning
+ deterministic safety and workflow constraints
```

This is not intended to be a generic chatbot over PDFs.

---

## 2. Brand and Client Information

### Confirmed project context

- The project is for an industrial AI startup.
- The user is the technical co-founder.
- The product is intended for industrial maintenance and field-service technicians.
- The initial technical focus is machine documentation, asset-aware retrieval, and evidence-first diagnosis.
- The system is advisory and read-only.

### Not available or not confirmed

The following information was not available in the accessible project context:

- Startup/company name.
- Public brand name.
- Logo or visual identity.
- Brand colors.
- Brand typography.
- Client or customer names.
- Specific pilot companies.
- Target industry beyond the broad industrial-maintenance context.
- Formal brand voice guide.
- Legal entity information.
- Product marketing positioning.
- Pricing or commercial model.

Do not invent these details in future work.

---

## 3. Writing Styles, Preferences, and Instructions

### User preferences

The user prefers practical, direct assistance focused on implementation and progress.

The user has repeatedly requested:

- Completing development days or weeks.
- Maintaining existing behavior.
- Running tests after changes.
- Creating commits during later work.
- No co-author tags in commits.
- Clear terminal commands that can be copied and pasted.
- Explanations in simple language when they do not understand the technical work.
- Manual testing instructions.
- Summaries suitable for explaining the work to a co-founder.

### Engineering instructions

Preserve working behavior before adding new features.

Do not:

- Build the complete product prematurely.
- Build the mobile app during the early prototype stages.
- Add PLC, SCADA, motor, valve, relay, or safety-system control.
- Implement physical machine-control integrations.
- Recommend repairs without sufficient evidence.
- Fabricate industrial facts.
- Create fake confidence scores.
- Treat technician-reported symptoms as verified measurements.
- Treat historical cases as authoritative OEM documentation.
- Hide deterministic evidence-selection logic inside an LLM prompt.
- Introduce microservices without a clear need.
- Overengineer the prototype.

### Safety posture

The system must remain advisory and read-only.

Potentially unsafe, invasive, destructive, restricted, or insufficiently supported actions should result in:

- `INSUFFICIENT_KNOWLEDGE`
- `ESCALATE`
- `SAFETY_BLOCK`
- Or an explicit supervision/review boundary.

The current safety implementation is a placeholder and is not a production safety engine.

### Communication style

When explaining the project:

- Lead with the outcome.
- Use plain language.
- Explain the business/technical meaning, not only implementation details.
- Clearly distinguish what is implemented from what is deferred.
- Report actual test results.
- Do not claim production readiness from small deterministic evaluations.

---

## 4. Important Work Completed

### Week 1

Week 1 established the repository, technical thesis, architecture, ingestion pipeline, retrieval baseline, grounded-answering boundary, and evaluation framework.

Completed capabilities:

- Technical PDF parsing.
- Page-preserving normalized document representation.
- Fixed-size chunking.
- Section-aware chunking.
- Local deterministic TF-IDF retrieval.
- Source and provenance preservation.
- Structured grounded-answer validation.
- A manually curated 12-case evaluation dataset.
- Reproducible Week 1 evaluation runner.
- Week 1 failure-analysis report.

Week 1 baseline results previously observed:

```text
Fixed-size retrieval hit rate: 80.0%
Section-aware retrieval hit rate: 80.0%
Correct source: 80.0%
Expected fact coverage: approximately 79.0%
Correct refusal: 0.0%
Unsupported claims: not measured
```

The Week 1 evaluation had four failed cases:

```text
case-009
case-010
case-011
case-012
```

The major Week 1 limitation was that retrieval did not yet have a strong asset-identity applicability boundary.

### Week 2

Week 2 moved from document retrieval toward evidence-first diagnostic reasoning.

Completed capabilities:

- Expanded `Asset` model.
- Added `AssetContext`.
- Added asset-aware retrieval filtering.
- Added manufacturer, family, model, revision, configuration, and site context.
- Added wrong-machine protection tests.
- Added `DiagnosticSession`.
- Added `Symptom`.
- Added `Observation`.
- Added `Hypothesis`.
- Added `EvidenceRequest`.
- Added diagnostic status enums.
- Added qualitative support levels instead of unsupported numeric probabilities.
- Added `DiagnosticAssessment`.
- Added diagnostic retrieval logs.
- Added Diagnostic Engine V0.
- Added multi-turn diagnostic sessions.
- Added observation corrections while preserving history.
- Added contradiction handling.
- Added duplicate evidence-request prevention.
- Added next-best-evidence selection.
- Added deterministic candidate scoring.
- Added safety placeholders.
- Added 15 diagnostic evaluation cases.
- Added Week 2 evaluation runner.
- Added Week 2 failure-analysis report.

Week 2 diagnostic evaluation results:

```text
Diagnostic cases: 15
Correct diagnostic status: 100%
Expected hypothesis coverage: 100%
Acceptable next evidence: 100%
Unsupported action absence: 100%
Provenance presence: 100%
Failed cases: 0
```

These results are from a small, deterministic, curated V0 evaluation set. They should not be interpreted as production diagnostic accuracy.

### Week 3

Week 3 added an application-service boundary around the diagnostic domain.

Completed capabilities:

- `DiagnosticSessionRepository` interface.
- In-memory repository implementation.
- Defensive copies to prevent accidental state mutation.
- `DiagnosticApplicationService`.
- Session creation.
- Session retrieval.
- Observation intake.
- Reassessment after new evidence.
- Explicit missing-session handling.
- Integration tests for the application workflow.
- Week 3 plan.
- Week 3 report.

The Week 3 workflow is:

```text
Create session
→ Initial assessment
→ Store session
→ Retrieve session
→ Add observation
→ Reassess
→ Store updated session
```

### Week 4

Week 4 added a versioned HTTP API around the Week 3 application service.

Completed capabilities:

- `GET /health`
- `POST /api/v1/diagnostic-sessions`
- `GET /api/v1/diagnostic-sessions/{session_id}`
- `POST /api/v1/diagnostic-sessions/{session_id}/observations`
- FastAPI application factory.
- Dependency injection for the application service.
- RFC 9457-style `application/problem+json` responses.
- Validation error handling.
- Missing-session error handling.
- HTTP contract tests.
- Week 4 plan.
- Week 4 report.

The last known test result was:

```text
39 tests passed
```

Known commits created during the later work:

```text
a621d01 feat: complete week two diagnostic foundation
0ae2ac7 feat: add diagnostic application service boundary
6f82bd6 feat: expose diagnostic workflow through versioned api
```

No co-author tags were requested for these commits.

---

## 5. Technical Architecture

The project is a Python modular monolith.

The current conceptual flow is:

```text
Asset
+
Reported Problem
+
Symptoms
+
Observations
        ↓
Diagnostic Application Service
        ↓
Diagnostic Session Service
        ↓
Diagnostic Query Builder
        ↓
Asset-Aware Retrieval
        ↓
Authoritative Knowledge
        ↓
Diagnostic Engine
        ↓
Hypotheses
        ↓
Evidence Candidates
        ↓
Deterministic Filtering
        ↓
Next Best Evidence
        ↓
Diagnostic Assessment
        ↓
Updated Session
        ↓
HTTP API / Future Client
```

The system deliberately distinguishes:

### Authoritative knowledge

Example:

```text
An OEM or government technical source describes compressor cooling behavior.
```

### Observation

Example:

```text
A technician recorded a discharge temperature of 108 C.
```

### AI inference

Example:

```text
Cooling restriction is a plausible hypothesis given the source and observation.
```

These must remain separate in the data model and provenance system.

---

## 6. Technical Workflows and Automation

### Environment setup

The project requires Python 3.12 or newer.

The project configuration declares:

```text
requires-python = >=3.12
```

Recommended setup:

```bash
cd /Users/anubhavkayal/Documents/ChatGPT/Vision

/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

If editable installation is unavailable because of network/build isolation issues:

```bash
python -m pip install pytest 'pydantic>=2.7,<3' 'PyMuPDF>=1.24,<2' 'fastapi>=0.115,<1'
```

Then use:

```bash
PYTHONPATH=. python -m pytest
```

### Run the full test suite

```bash
PYTHONPATH=. python -m pytest
```

Expected last-known result:

```text
39 passed
```

### Run Week 1 evaluation

```bash
PYTHONPATH=. python -m evaluation.run --top-k 5
```

### Run Week 2 evaluation

```bash
PYTHONPATH=. python -m evaluation.diagnostic_run
```

Expected:

```text
Failed cases: []
```

### Run compilation and diff checks

```bash
python -m compileall -q backend ingestion evaluation
git diff --check
```

### Week 1 evaluation output

The Week 1 result is written to:

```text
evaluation/results/week1_baseline.json
```

### Week 2 evaluation output

The Week 2 result is written to:

```text
evaluation/results/week2_diagnostic_baseline.json
```

These evaluation results may be ignored by Git depending on the current `.gitignore`.

---

## 7. Reusable Prompts and Templates

### Continue implementation

```text
Continue as the senior AI systems engineer on the existing industrial AI prototype.

First inspect the complete repository, README.md, architecture documentation, current evaluation results, existing tests, and current git status.

Preserve working behavior.

Implement only the requested milestone.

Do not build unrelated product features.

Run the relevant tests, compile checks, and diff validation.

Report:
- what changed,
- what was tested,
- actual results,
- known limitations,
- files changed,
- whether a commit was created.
```

### Start a new development week

```text
Start Week [N] of the industrial AI prototype.

Use the existing repository and previous week report.

Before changing code:
- inspect the repository,
- inspect README.md,
- inspect architecture documentation,
- inspect previous evaluation results,
- inspect existing tests,
- inspect current git status.

Define a bounded objective for this week.

Implement the objective incrementally.

Preserve the read-only advisory safety posture.

Do not add PLC, SCADA, actuator, repair-execution, or physical-control integrations.

Run all regression tests and add tests for the new behavior.

Create documentation and a failure-analysis report.

Commit the work in logical commits without a co-author tag.
```

### Explain to a co-founder

```text
Explain this week in simple language for a technical co-founder.

Cover:
1. What problem we were solving.
2. What we built.
3. How the system behaves end to end.
4. What the test results mean.
5. What is still only a prototype.
6. What we deliberately did not build.
7. What we should do next.
```

### Manual testing request

```text
Give me a manual test checklist for this week.

Include:
- exact terminal commands,
- expected output,
- happy path,
- unsupported input,
- wrong-machine input,
- contradictory evidence,
- duplicate request behavior,
- safety-sensitive behavior,
- provenance/source verification,
- what counts as a failure.
```

### Commit request

```text
Review the current changes, run the relevant tests, and create a conventional commit.

Do not add a co-author tag.

Before committing:
- report the files being included,
- exclude unrelated files,
- run tests,
- run compile checks,
- run git diff --check.

After committing, report the commit hash and message.
```

---

## 8. Pending Tasks and Next Steps

### Immediate technical next steps

1. Verify the repository after migration to Codex CLI.
2. Confirm the current branch and remote configuration.
3. Run the complete test suite.
4. Re-run Week 1 and Week 2 evaluations.
5. Remove or ignore unrelated `.DS_Store` files.
6. Confirm whether the latest commits have been pushed to GitHub.
7. Review the Week 4 API contract with a domain stakeholder.
8. Add API documentation or OpenAPI review if needed.
9. Add authentication and authorization before real deployment.
10. Add persistent storage only after the repository contract is reviewed.

### Recommended future work

- Domain-reviewed diagnostic evaluation cases.
- Stronger refusal and safety cases.
- Persistent database-backed repository.
- Authentication and authorization.
- Audit logging.
- Rate limiting.
- API deployment configuration.
- Better retrieval for safety and unsupported-knowledge cases.
- Dense embeddings and reranking experiments.
- Provider-backed structured generation behind existing provenance validation.
- Multimodal evidence processing.
- Technician-facing mobile or web client.
- Verification workflow.
- Structured service records.
- Historical service-case learning with authority distinctions.

### Explicitly deferred

- PLC integration.
- SCADA integration.
- Motor, valve, relay, or actuator control.
- Automatic repair execution.
- Production safety policy engine.
- Autonomous physical action.
- Mobile application before the backend contracts are stable.

---

## 9. Relevant Files and Resources

### Core documentation

```text
README.md
docs/THESIS.md
docs/architecture.md
docs/week-01-report.md
docs/week-02-plan.md
docs/week-02-report.md
docs/week-03-plan.md
docs/week-03-report.md
docs/week-04-plan.md
docs/week-04-report.md
```

### Diagnostic documentation

```text
docs/diagnostic-model.md
docs/diagnostic-engine-v0.md
docs/diagnostic-session-loop.md
docs/next-best-evidence.md
```

### Domain and application code

```text
backend/app/models.py
backend/app/grounded_answering.py
backend/app/api.py
backend/app/diagnostics/models.py
backend/app/diagnostics/engine.py
backend/app/diagnostics/evidence_selection.py
backend/app/diagnostics/session.py
backend/app/diagnostics/repository.py
backend/app/diagnostics/application.py
```

### Ingestion and retrieval

```text
ingestion/models.py
ingestion/pdf_parser.py
ingestion/chunking.py
ingestion/pipeline.py
ingestion/retrieval.py
```

### Evaluation

```text
evaluation/run.py
evaluation/diagnostic_run.py
evaluation/diagnostic_models.py
evaluation/cases/week1_v0.json
evaluation/cases/week2_diagnostic_v0.json
evaluation/results/week1_baseline.json
evaluation/results/week2_diagnostic_baseline.json
```

### Tests

```text
backend/tests/test_models.py
backend/tests/test_ingestion.py
backend/tests/test_retrieval.py
backend/tests/test_grounded_answering.py
backend/tests/test_diagnostic_models.py
backend/tests/test_diagnostic_engine.py
backend/tests/test_diagnostic_session.py
backend/tests/test_evidence_selection.py
backend/tests/test_diagnostic_evaluation.py
backend/tests/test_diagnostic_application.py
```

### Sample data

```text
sample_data/manual.json
sample_data/parsed/doe-ee-1340.sample.json
```

The sample source is a technical document about industrial compressed-air systems.

---

## 10. Important Decisions and Constraints

### Modular monolith

The project intentionally uses a modular monolith.

Microservices are deferred until there is a demonstrated need.

### Deterministic baseline first

The project uses a deterministic local TF-IDF retrieval baseline before introducing embeddings or reranking.

### Asset-aware retrieval

Known identity conflicts should be filtered rather than silently accepted.

Generic documents may remain eligible when they do not specify a conflicting model.

### Qualitative hypotheses

The system uses qualitative support levels such as:

```text
WEAKLY_SUPPORTED
SUPPORTED
STRONGLY_SUPPORTED
UNKNOWN
```

Do not invent numeric probabilities without a calibrated model.

### Evidence-first reasoning

The system should not follow:

```text
SYMPTOM → REPAIR ANSWER
```

It should follow:

```text
SYMPTOM
→ POSSIBLE CAUSES
→ MISSING INFORMATION
→ NEXT OBSERVATION
→ UPDATED HYPOTHESES
```

### Provenance

Diagnostic assessments retain retrieved source information.

Sources should remain traceable to document, page, section, and supporting text.

### Safety

The current safety statuses are:

```text
ALLOWED_ADVISORY
REQUIRES_SUPERVISION
SAFETY_BLOCK
UNKNOWN
```

These are placeholders and must not be described as a production safety engine.

### No machine control

No code should control or write to:

- PLCs.
- SCADA systems.
- Motors.
- Valves.
- Relays.
- Industrial controllers.
- Safety systems.

### No silent history deletion

Corrected observations must preserve the original observation and identify the correction relationship.

### No hidden reasoning requirement

The system should expose concise structured evidence-based justification, not private chain-of-thought.

---

## 11. Continuing in Codex CLI

### First commands to run

```bash
cd /Users/anubhavkayal/Documents/ChatGPT/Vision
git status --short --branch
git log --oneline -10
```

Then activate or create the Python environment:

```bash
source .venv/bin/activate
python --version
```

If `.venv` does not exist:

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

### Regression checks

```bash
PYTHONPATH=. python -m pytest
PYTHONPATH=. python -m evaluation.run --top-k 5
PYTHONPATH=. python -m evaluation.diagnostic_run
```

### Before new work

Read:

```text
README.md
docs/THESIS.md
docs/architecture.md
docs/week-01-report.md
docs/week-02-report.md
docs/week-03-report.md
docs/week-04-report.md
```

Inspect:

```bash
git status
git log --oneline --decorate -10
git remote -v
```

### Current known repository state

The last known branch state was:

```text
main...origin/main [ahead 3]
```

The last known unrelated untracked file was:

```text
sample_data/.DS_Store
```

Do not automatically commit unrelated generated files.

### Git instructions

The user currently permits commits and requested:

- Keep committing during implementation.
- Do not add a co-author tag.
- Use logical conventional commit messages.
- Do not commit unrelated files.
- Report commit hashes after committing.

### Information unavailable

This migration document cannot confirm:

- Whether the latest commits were pushed to GitHub.
- The current GitHub remote URL.
- Whether the local repository still exists at the previous filesystem path.
- Whether another developer has modified the repository since the last known state.
- Whether there are newer project chats containing a changed roadmap.
- Whether Week 5 requirements have been defined.
- Whether FastAPI dependencies are installed in the migrated CLI environment.
- Whether the existing `.venv` remains usable after migration.
- Any production credentials, secrets, cloud configuration, or deployment setup.

Treat these as verification tasks in Codex CLI rather than assumed facts.