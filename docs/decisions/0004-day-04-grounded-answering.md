# Decision 0004: Day 4 grounded answer boundary

## Decision

Place a provider-neutral `ModelProvider` protocol above retrieval. The model receives only the retrieved chunks, must return structured JSON, and is accepted only when every cited source matches retrieved document/page/section/text evidence.

Malformed output, unknown citations, or absent retrieval evidence become `INSUFFICIENT_KNOWLEDGE` rather than being passed through.

## What this does not solve

The validator checks citation identity and exact supporting excerpts; it does not prove that every sentence in the answer is semantically entailed by those excerpts. That requires a later deterministic claim checker or separately measured judge, and must not be confused with provenance validation.
