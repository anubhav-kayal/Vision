# Physical AI OS

Industrial maintenance intelligence prototype with a runnable local diagnostic API.

The prototype tests whether machine-specific documentation, asset identity, structured evidence, and deterministic constraints can support grounded technician assistance. It is advisory and read-only: it does not control machinery or claim authority over OEM documentation.

## Current status

The local pilot includes asset/document registration, relational persistence,
versioned PDF ingestion, applicable document retrieval, approved diagnostic
playbooks, image intake/confirmation, optional hosted model adapters, and complete
assessment history. PostgreSQL full-text/pgvector search is optional.

Start with [the pilot runbook](docs/pilot-runbook.md). Real generator guidance
requires an authorized manual and domain-approved playbooks; the bundled pilot
evaluation is synthetic and does not measure industrial accuracy.

## Repository layout

```text
physical-ai-os/
├── backend/app/           # Domain, application, persistence, and API boundaries
├── backend/tests/         # Automated tests
├── ingestion/             # PDF parsing, chunking, and retrieval channels
├── evaluation/            # Reproducible retrieval and diagnostic evaluations
├── docs/                  # Thesis, architecture, decisions, and reports
└── sample_data/           # Curated, legally usable experiment inputs
```

## Local setup

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

The package is intentionally local-first. Environment variables for future model providers belong in a local `.env` file; never commit secrets.

## Current checks

```bash
pytest
python -m compileall backend
```

Run `sh scripts/check.sh` for all pilot checks. See [docs/THESIS.md](docs/THESIS.md)
and [docs/architecture.md](docs/architecture.md) for the technical direction and scope.
