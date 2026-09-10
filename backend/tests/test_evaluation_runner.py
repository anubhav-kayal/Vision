from evaluation.run import run_evaluation


def test_evaluation_runner_records_reproducibility_and_metrics() -> None:
    report = run_evaluation(
        "sample_data/parsed/doe-ee-1340.full.json",
        "evaluation/cases/week1_v0.json",
        top_k=5,
    )

    assert report["embedding_model"] == "tfidf-local"
    assert report["retrieval_configuration"]["top_k"] == 5
    assert set(report["strategies"]) == {"fixed_size", "section_aware"}
    assert report["strategies"]["section_aware"]["metrics"]["unsupported_claim_rate"] is None
