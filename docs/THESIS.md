# Week 1 Technical Thesis

## Hypothesis

General multimodal AI combined with machine-specific knowledge, asset identity, structured reasoning, and deterministic safety/workflow constraints may improve industrial technician troubleshooting without requiring a separately trained model for every machine.

Week 1 tests only the earliest measurable part of this hypothesis: whether a small, versioned technical knowledge base can be retrieved and used to produce conservative, precisely cited responses.

## Technical questions

1. Can we retrieve the correct machine information?
2. Can the system answer questions using only authoritative machine documentation?
3. Can the system provide exact provenance?
4. Can the model distinguish supported knowledge from unsupported inference?
5. Can it reason from symptoms?
6. Can it ask useful diagnostic questions?
7. Can it interpret technician evidence?
8. Can unsafe or unsupported actions be constrained?
9. Can outcomes be represented structurally?
10. Can the architecture eventually generalize to another machine family?

## Week 1 success criteria

- A legally usable equipment technical document is selected and its identity is recorded.
- Document content can be normalized without losing page-level provenance.
- Baseline retrieval can be evaluated independently of answer generation.
- Grounded responses distinguish supported, partial, and insufficient knowledge.
- At least 10 reproducible cases measure retrieval, provenance, fact coverage, and refusal behavior.
- Failures are preserved and classified rather than hidden behind demo quality.

## Explicitly out of scope

Week 1 will not build a mobile application, authentication, billing, dashboards, cloud/AWS infrastructure, Kubernetes, microservices, smart glasses, AR/VR, robotics, predictive maintenance, PLC/IoT control, custom model training, fine-tuning, multi-company tenancy, complex knowledge graphs, or sales tooling.

The prototype will not issue commands to physical systems. It will remain advisory and read-only, and it will not treat an AI inference as OEM documentation.

## Product principles

- Asset identity must be explicit.
- Authority and document revision must remain representable.
- Every machine-specific claim should have provenance.
- Unsupported evidence should produce uncertainty or escalation, not invented instructions.
- Retrieval quality must be measured before optimizing generation quality.
- The simplest modular monolith that supports these experiments is preferred.

## Current assumptions

- The first experiment uses one equipment family and one legally usable manual.
- Local deterministic tests are the baseline; external model calls will be optional and configured through environment variables.
- Schemas will evolve as real documents and evaluation cases expose missing fields.
