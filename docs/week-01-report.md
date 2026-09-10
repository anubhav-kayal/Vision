# Week 1 Report

## What we built

- A Python modular monolith with strict Pydantic domain contracts.
- Page-preserving PDF ingestion with printed-page extraction and conservative section detection.
- Fixed-size and section-aware chunking.
- A deterministic local TF-IDF vector retrieval baseline.
- A provider-neutral grounded-answer boundary with structured output and provenance validation.
- A manually curated 12-case evaluation dataset.
- A reproducible evaluation runner with deterministic retrieval metrics.

The system remains advisory and read-only. No model was allowed to control or issue commands to physical equipment.

## Dataset/manual used

The experiment uses the U.S. Department of Energy publication `DOE/EE-1340`, *Improving Compressed Air System Performance: A Sourcebook for Industry, Third Edition*. The downloaded 114-page PDF is kept locally under `sample_data/raw/` and ignored by Git. The repository stores its manifest and parsed inspection sample.

This is a government technical sourcebook for industrial compressed-air systems, not a model-specific OEM service manual. That makes it useful for ingestion and provenance experiments, but insufficient for asset-specific troubleshooting.

## Architecture

```text
DOE PDF
  → page-preserving parser
  → fixed-size / section-aware chunks
  → TF-IDF vector retrieval
  → bounded provider-neutral grounded-answer layer
  → deterministic evaluation runner
```

The answer layer accepts only retrieved context and rejects malformed output or citations that do not match retrieved evidence. It does not yet prove semantic entailment for every sentence.

## Evaluation configuration

- Cases: 12
- Top-k: 5
- Fixed-size chunks: 1,200 characters with 150-character overlap
- Section-aware chunks: 1,800-character maximum
- Vector baseline: local TF-IDF cosine similarity
- Model: not run
- Embedding model: `tfidf-local`
- Prompt version: not applicable
- Run command: `python -m evaluation.run --top-k 5`
- Raw result: `evaluation/results/week1_baseline.json` (local, ignored by Git)

## Results

| Strategy | Retrieval hit rate | Correct source | Expected fact coverage | Correct refusal | Unsupported claims |
|---|---:|---:|---:|---:|---|
| Fixed-size | 80.0% | 80.0% | 79.0% | 0.0% | Not measured |
| Section-aware | 80.0% | 80.0% | 77.8% | 0.0% | Not measured |

Unsupported-claim rate is not reported as zero. No live/generated model output was evaluated, so that metric is currently unavailable.

## Failed cases

- `case-009`: safety lookup about cooling before service was not retrieved in the top five.
- `case-010`: annual maintenance schedule lookup was not retrieved in the top five.
- `case-011`: an ambiguous question returned generic compressor content instead of being recognized as insufficient.
- `case-012`: a wrong-machine John Deere question returned generic compressor content instead of being filtered out.

All four failures were classified as `RETRIEVAL_FAILURE` in the current baseline. This classification is intentionally conservative: the answer layer cannot safely compensate for missing or irrelevant context.

## Failure categories

| Category | Count | Interpretation |
|---|---:|---|
| RETRIEVAL_FAILURE | 4 | Expected pages were missed or irrelevant generic chunks were returned. |
| INGESTION_FAILURE | 0 | The selected pages were parsed and retained provenance. |
| CHUNKING_FAILURE | 0 confirmed | Chunking may contribute to misses, but the current runner cannot isolate it from ranking. |
| GENERATION_FAILURE | Not measured | No live model output was used. |
| HALLUCINATION | Not measured | No live model output was used. |
| PROVENANCE_FAILURE | 0 in tests | Structured citation validation passed its deterministic tests. |

## Important discoveries

1. Section-aware chunking did not improve retrieval hit rate over the fixed-size baseline on this small dataset.
2. Fixed-size chunks had slightly higher expected-fact coverage, but this is not enough evidence to select them generally.
3. Lexical overlap is dangerous for wrong-machine and underspecified queries: generic compressor terms can produce plausible but irrelevant context.
4. Provenance validation is implementable deterministically, but provenance alone does not establish that every answer sentence is supported.
5. A generic technical sourcebook is not a substitute for exact asset identity or an OEM service manual.

## Architectural decisions

- Keep ingestion, retrieval, and answering behind replaceable boundaries.
- Use local deterministic retrieval before introducing dense embeddings or model calls.
- Preserve document ID, PDF page, printed page, section, chunk ID, authority, and supporting text.
- Treat unsupported-claim metrics as unavailable until actual generated answers exist.
- Prefer `INSUFFICIENT_KNOWLEDGE` over an answer when evidence is absent or citations fail validation.

## Technical debt

- No asset/model identity filter exists in retrieval.
- No hybrid lexical+dense retrieval or reranker exists.
- No retrieval confidence threshold exists for refusal.
- The section detector is heuristic and needs evaluation on varied manual layouts.
- The evaluation runner does not yet score semantic answer correctness or unsupported claims.
- The current source is not model-specific.
- The full parsed corpus and evaluation result are local ignored artifacts rather than versioned experiment fixtures.

## Questions requiring domain expertise

- What minimum asset identity fields must be present before any maintenance guidance is shown?
- Which safety procedures require hard blocking rather than a cited advisory response?
- Which source authority should outrank a government guide when it conflicts with an OEM manual?
- What evidence would a technician consider sufficient to distinguish a generic compressor issue from an asset-specific fault?

## Recommended Week 2 experiments

1. Add an explicitly licensed or supplied model-specific OEM manual and test asset filtering.
2. Add retrieval thresholds and an `INSUFFICIENT_KNOWLEDGE` decision for low-confidence or wrong-asset results.
3. Compare TF-IDF with a local dense embedding model and a simple hybrid ranker.
4. Connect one model provider behind `ModelProvider` and measure structured-answer accuracy, refusal behavior, unsupported claims, and provenance.
5. Expand the evaluation set with near-miss asset identities, conflicting revisions, fault-code lookups, and safety-boundary cases.
