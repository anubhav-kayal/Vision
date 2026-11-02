# Vision — Codex CLI Instructions

## Project Location
/Volumes/Anubhav SSD/Vision/

## Session Initialization
At the start of every session:
1. Read CONTEXT.md and README.md.
2. Review docs/THESIS.md and docs/architecture.md.
3. Review the latest weekly development report.
4. Check git status and recent commits.
5. Inspect existing code before making changes.

The repository is the source of truth for current implementation.
CONTEXT.md provides historical decisions and progress.

## Project Architecture
- Python 3.12+ and FastAPI.
- Maintain the modular monolith architecture.
- Preserve asset-aware document retrieval.
- Maintain evidence-first diagnostic reasoning.
- Preserve source provenance and diagnostic history.
- Keep deterministic evidence-selection logic outside LLM prompts.
- Avoid unnecessary microservices and premature features.

## Safety Rules
- The system must remain advisory and read-only.
- Never implement PLC, SCADA or physical machine control.
- Never recommend unsupported industrial repairs.
- Never fabricate industrial facts or confidence scores.
- Maintain explicit safety and escalation boundaries.
- Do not treat unverified observations as measurements.
- Never describe the current safety placeholders as production-ready.

## Development Workflow
1. Understand the requested development milestone.
2. Inspect existing implementation.
3. Preserve working functionality.
4. Make focused changes.
5. Add relevant tests.
6. Run regression tests and evaluations.
7. Report actual results and remaining limitations.

## Testing
Run relevant checks:

PYTHONPATH=. python -m pytest
PYTHONPATH=. python -m evaluation.run --top-k 5
PYTHONPATH=. python -m evaluation.diagnostic_run
python -m compileall -q backend ingestion evaluation
git diff --check

## Git Rules
- Preserve Git history.
- Never force-push or delete branches without permission.
- Create logical conventional commits when requested.
- Never add co-author tags.
- Do not commit unrelated files.
- Report commit hashes.
- Never push without authorization.

## SSD Rules
- All project work stays on the external SSD.
- Do not use the old local Vision directory.
- Do not modify unrelated repositories.
- Stop if the SSD is unavailable or unwritable.

## Migration
- Preserve CONTEXT.md and AGENTS.md.
- Do not discard legitimate uncommitted changes.
- Do not start Week 5 until migration verification passes.
- Fix migration issues before implementing new features.

## Communication
- Explain changes clearly.
- Distinguish implemented, pending and deferred features.
- Report actual tests, not assumed results.
- Provide copy-paste terminal commands when useful.
