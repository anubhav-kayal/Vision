# Week 2 Plan - Day 1 Review and Asset Context

## Strongest Week 1 capability

The prototype can parse a real technical PDF, preserve page/section provenance, retrieve ranked chunks, and validate structured citations against retrieved evidence. The evaluation is reproducible and the failures are visible.

## Weakest Week 1 capability

Retrieval has no asset applicability boundary. It can return generic compressor information for an ambiguous question or a question about a different machine. Correct refusal was 0% for the two insufficient-knowledge cases.

## Retrieval failures

The Week 1 run missed two maintenance/safety cases at top-k=5 and returned generic content for two unsupported/wrong-machine cases. Fixed-size and section-aware chunking both reached 80% retrieval hit rate; neither solved identity contamination.

## Hallucination and provenance failures

No live model output was evaluated, so hallucination and unsupported-claim rates remain unmeasured. Deterministic provenance validation passed its tests and rejects unknown chunks, pages, sections, or supporting excerpts.

## Architectural issues

- Asset identity was represented only as an unused domain model.
- Retrieval accepted a query without identity context.
- Generic and model-specific knowledge had no applicability filter.
- Refusal had no confidence or identity-mismatch gate.

## Technical debt to fix now

- Add `AssetContext` and filter known manufacturer, family, model, and revision conflicts.
- Add tests for same-family/different-model, same-model/different-revision, and similar-fault cross-contamination.
- Keep evaluation of generic documents explicit rather than labeling them OEM-specific.

## Technical debt to defer

Dense embeddings, reranking, PostgreSQL/pgvector, APIs, live model integration, multimodal evidence processing, and policy engines remain deferred until the identity boundary is tested.

## Day 1 definition of done

An asset can be represented explicitly, converted to an `AssetContext`, and passed to retrieval. Known conflicting documents are excluded while generic family guidance remains eligible. Diagnostic reasoning begins only after these tests pass.
