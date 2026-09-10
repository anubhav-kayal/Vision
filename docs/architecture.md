# Initial Architecture

## Day 1 boundary

The repository is a Python modular monolith. Day 1 contains only domain contracts and documentation. Later stages will add ingestion, retrieval, and grounded generation as replaceable modules rather than coupling them to a provider or API framework.

```text
source manual
    ↓
ingestion: parse → preserve pages → identify sections → chunk → attach metadata
    ↓
retrieval: lexical/vector baseline → ranked chunks with provenance
    ↓
answering: provider interface → structured grounded response
    ↓
evaluation: fixed cases → deterministic metrics → preserved report
```

## Domain contracts

`backend/app/models.py` contains the minimum shared vocabulary:

- `Asset`: identifies the physical asset and configuration.
- `KnowledgeDocument`: records machine/document identity, revision, source, and authority.
- `ServiceCase`: captures symptoms, observations, and eventual verified outcome fields.
- `GroundedSource` and `GroundedAnswer`: define the provenance-bearing response boundary for later retrieval/LLM work.

The authority level is an enum today so invalid values fail early, while the ordering/policy decision is intentionally deferred. The model can represent the planned hierarchy without pretending that the policy engine already exists.

## Replacement boundaries

- A retrieval interface should return chunks plus scores and provenance; storage may start local and later move to PostgreSQL/pgvector.
- A model-provider interface should accept a bounded context and return a validated `GroundedAnswer`.
- Evaluation must record configuration and distinguish deterministic metrics from model-graded metrics.

The Day 2 ingestion boundary is `ingestion.pdf_parser.parse_pdf`, which returns page-preserving normalized text, and `ingestion.chunking`, which exposes fixed-size and section-aware strategies. Day 3 adds `ingestion.retrieval.TfidfIndex`, a deterministic local sparse-vector baseline that returns ranked chunks with provenance. It is deliberately not a semantic embedding model yet. FastAPI is not introduced because there is no useful HTTP contract yet. Pydantic is used for the domain boundary and pytest for executable checks.

## Safety posture

The system is advisory and read-only. It must not control PLCs, valves, motors, or other physical systems. Future workflow states such as `NEED_EVIDENCE`, `SAFETY_BLOCK`, and `ESCALATE` should be explicit rather than inferred from a free-form answer.

## Known technical debt

- The current sample is a government technical sourcebook rather than an OEM model-specific service manual; model-specific authority and asset matching remain a later experiment.
- Authority precedence is represented but not enforced.
- Retrieval, embedding, and provider interfaces have not been implemented.
- The current retrieval baseline has no asset-identity filter, dense embeddings, reranker, or hybrid score.
- Dates and document source validation will need tighter rules once real inputs arrive.
