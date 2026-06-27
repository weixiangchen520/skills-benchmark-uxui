from skills_benchmark_uxui.models.scoring import Score, Verdict, aggregate_verdicts


def test_verdict_and_pass_k_aggregation() -> None:
    verdicts = [
        Verdict.from_scores(
            task_id="U01en_demo",
            trial=1,
            required_dimensions=["completion", "robustness"],
            pass_threshold=0.8,
            component_scores=[
                Score(
                    component="content",
                    passed=True,
                    score=0.9,
                    dimension="completion",
                    weight=0.7,
                ),
                Score(
                    component="runs",
                    passed=True,
                    score=1.0,
                    dimension="robustness",
                    weight=0.3,
                ),
            ],
        ),
        Verdict.from_scores(
            task_id="U01en_demo",
            trial=2,
            required_dimensions=["completion", "robustness"],
            pass_threshold=0.8,
            component_scores=[
                Score(
                    component="content",
                    passed=True,
                    score=0.85,
                    dimension="completion",
                    weight=0.7,
                ),
                Score(
                    component="runs",
                    passed=True,
                    score=1.0,
                    dimension="robustness",
                    weight=0.3,
                ),
            ],
        ),
    ]

    summary = aggregate_verdicts(verdicts, required_trials=2)

    assert summary.pass_k is True
    assert summary.success_rate == 1.0
    assert summary.component_pass_rates == {"content": 1.0, "runs": 1.0}


def test_pass_k_requires_all_required_trials_to_pass() -> None:
    verdicts = [
        Verdict(task_id="U01en_demo", trial=1, score=1.0, passed=True),
        Verdict(task_id="U01en_demo", trial=2, score=0.0, passed=False),
    ]

    summary = aggregate_verdicts(verdicts, required_trials=2)

    assert summary.pass_k is False
    assert summary.success_rate == 0.5
