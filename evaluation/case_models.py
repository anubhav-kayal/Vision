"""Schemas for the manually curated evaluation dataset."""

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models import AnswerStatus


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: str = Field(min_length=1)
    case_type: str = Field(min_length=1)
    query: str = Field(min_length=1)
    asset_context: dict[str, str | None]
    expected_source_document: str | None = None
    expected_printed_pages: list[str] = Field(default_factory=list)
    expected_sections: list[str] = Field(default_factory=list)
    expected_key_facts: list[str] = Field(default_factory=list)
    expected_status: AnswerStatus
    notes: str = Field(min_length=1)


def load_cases(path: str) -> list[EvaluationCase]:
    """Load and validate every case in a JSON array."""

    import json
    from pathlib import Path

    raw_cases = json.loads(Path(path).read_text(encoding="utf-8"))
    return [EvaluationCase.model_validate(case) for case in raw_cases]
