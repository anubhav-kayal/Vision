from evaluation.diagnostic_run import run_diagnostic_evaluation


def test_week2_diagnostic_evaluation_is_reproducible_and_clean() -> None:
    report = run_diagnostic_evaluation(
        "sample_data/parsed/doe-ee-1340.sample.json",
        "evaluation/cases/week2_diagnostic_v0.json",
    )

    assert report["case_count"] == 15
    assert report["failed_cases"] == []
    assert report["metrics"]["correct_status_rate"] == 1.0
    assert report["metrics"]["provenance_presence_rate"] == 1.0
