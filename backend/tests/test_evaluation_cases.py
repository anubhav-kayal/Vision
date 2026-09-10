from pathlib import Path

from backend.app.models import AnswerStatus
from evaluation.case_models import load_cases


def test_week1_dataset_has_diverse_valid_cases() -> None:
    path = Path("evaluation/cases/week1_v0.json")
    cases = load_cases(str(path))

    assert len(cases) == 12
    assert {case.expected_status for case in cases} == {
        AnswerStatus.SUPPORTED,
        AnswerStatus.INSUFFICIENT_KNOWLEDGE,
    }
    assert {case.case_type for case in cases} >= {
        "straightforward_lookup",
        "specification_lookup",
        "procedure_lookup",
        "safety_lookup",
        "ambiguous_question",
        "wrong_machine_question",
    }


def test_supported_cases_have_source_and_expected_facts() -> None:
    cases = load_cases("evaluation/cases/week1_v0.json")

    for case in cases:
        if case.expected_status is AnswerStatus.SUPPORTED:
            assert case.expected_source_document == "doe-ee-1340"
            assert case.expected_printed_pages
            assert case.expected_sections
            assert case.expected_key_facts
