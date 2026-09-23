# Week 2 Day 4 - Multi-turn Diagnostic Session

`DiagnosticSessionService` orchestrates the state transition:

```text
SESSION STATE → ASSESS → RECORD REQUEST → ADD OBSERVATION → REASSESS
```

Observations are append-only. A correction adds a new observation with `supersedes_observation_id` and `correction_reason`; the original remains in history and is excluded from active evidence after being marked superseded.

Hypotheses are merged by stable ID rather than duplicated. Visual evidence containing `dirty`, `blocked`, or `restricted` strengthens the V0 temperature hypotheses; evidence containing `clean`, `normal`, or `clear` marks them contradicted. This is a narrow deterministic test path, not a general diagnostic model.

Evidence requests are recorded and identical type/target requests are not added twice. The engine reuses Week 1 retrieval and keeps retrieval logs and source references in the assessment/session boundary.

The loop remains advisory. It does not execute a requested action, authorize unsafe work, or recommend component replacement.
