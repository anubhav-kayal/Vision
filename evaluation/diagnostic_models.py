"""Schemas for the deterministic Week 2 diagnostic evaluation set."""

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models import AssetContext
from backend.app.diagnostics.models import DiagnosticStatus, Observation


class DiagnosticCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    asset_context: AssetContext
    initial_problem: str = Field(min_length=1)
    initial_observations: list[Observation] = Field(default_factory=list)
    expected_hypotheses: list[str] = Field(default_factory=list)
    acceptable_next_observations: list[str] = Field(default_factory=list)
    unacceptable_actions: list[str] = Field(default_factory=list)
    expected_status: DiagnosticStatus
    source_references: list[str] = Field(default_factory=list)


def load_diagnostic_cases(path: str) -> list[DiagnosticCase]:
    import json
    from pathlib import Path

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [DiagnosticCase.model_validate(item) for item in raw]
