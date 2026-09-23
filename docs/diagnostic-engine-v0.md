# Diagnostic Engine V0

## Scope

`DiagnosticEngineV0` is a deterministic, evidence-first assessment layer. It reuses the Week 1 `TfidfIndex`, accepts an `AssetContext`, and returns a structured `DiagnosticAssessment`. It does not execute repairs, control equipment, or claim a diagnosis from symptoms alone.

## Current behavior

For compressor temperature/overheating problems, the engine:

1. Builds an observable retrieval query from asset identity, the reported problem, symptoms, and observations.
2. Applies the asset-context applicability filter.
3. Records retrieved chunk IDs, scores, and identity filters.
4. Produces weakly supported hypotheses for cooling-surface fouling and air-intake/filter restriction when the retrieved documentation supports those concepts.
5. Requests a discharge-temperature measurement when no temperature observation exists.
6. Requests a supervised visual inspection after a temperature observation exists.
7. Returns `INSUFFICIENT_KNOWLEDGE` for unsupported problem patterns or empty applicable retrieval.

## Conservative boundaries

The engine never recommends component replacement or repair execution. Evidence requests include source references and an explicit safety status. A `REQUIRES_SUPERVISION` request is not equivalent to permission to perform the action; a future interface must enforce that boundary.

The engine uses qualitative `WEAKLY_SUPPORTED` hypotheses. It does not emit numeric probabilities because the prototype has no calibration data. It also does not claim that the hypotheses are mutually exclusive or exhaustive.

## Known limitations

- V0 has one deterministic problem pattern and is not a general diagnostic engine.
- Hypothesis generation is rule-based and does not yet distinguish evidence strength beyond qualitative labels.
- Retrieval can still return generic guidance; model-specific and revision-specific documents require the asset filter.
- Contradictory evidence, multi-turn session updates, corrected observations, and next-best-evidence ranking are later stages.
