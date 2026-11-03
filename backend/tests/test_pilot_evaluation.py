from evaluation.pilot_run import run


def test_pilot_workflow_evaluation_is_explicitly_synthetic():
    report = run()
    assert report["metrics"]["cases"] == 15
    assert report["failed_cases"] == []
    assert report["industrial_accuracy"] == "NOT_MEASURED"
    assert report["model_quality"] == "NOT_MEASURED"
