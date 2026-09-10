# Physical AI OS

Week 1 technical prototype for an industrial maintenance intelligence layer.

The prototype tests whether machine-specific documentation, asset identity, structured evidence, and deterministic constraints can support grounded technician assistance. It is advisory and read-only: it does not control machinery or claim authority over OEM documentation.

## Day 1 status

Day 1 establishes the repository, technical thesis, initial architecture, and minimal domain schemas. Ingestion, retrieval, answer generation, and evaluation are intentionally deferred until the following days.

## Repository layout

```text
physical-ai-os/
├── backend/app/           # Domain models and future application boundary
├── backend/tests/         # Automated tests
├── ingestion/             # Future document parsing and chunking pipeline
├── evaluation/            # Future cases, runners, and experiment results
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

See [docs/THESIS.md](docs/THESIS.md) and [docs/architecture.md](docs/architecture.md) for the current technical direction and explicit scope.
