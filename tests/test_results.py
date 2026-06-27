from skills_benchmark_uxui.models.scoring import Verdict
from skills_benchmark_uxui.models.suite import Suite
from skills_benchmark_uxui.models.trace import Trace, TrajectoryStep
from skills_benchmark_uxui.results import (
    default_trace_path,
    load_trace,
    load_verdicts,
    summarize_by_suite,
    summarize_suite,
    summaries_to_markdown,
    summarize_by_task,
    write_trace,
    write_verdict,
)


def test_write_load_and_summarize_verdicts(tmp_path) -> None:
    path = tmp_path / "results" / "verdicts.jsonl"
    write_verdict(path, Verdict(task_id="U01en_demo", trial=1, score=1.0, passed=True))
    write_verdict(path, Verdict(task_id="U01en_demo", trial=2, score=0.0, passed=False))

    verdicts = load_verdicts(path)
    summaries = summarize_by_task(verdicts, required_trials=2)

    assert len(verdicts) == 2
    assert summaries["U01en_demo"].pass_k is False
    assert summaries["U01en_demo"].success_rate == 0.5
    assert "| `U01en_demo` | 2/2 | no | 0.500 | 0.500 |" in summaries_to_markdown(summaries)


def test_write_load_trace_and_default_path(tmp_path) -> None:
    trace = Trace(
        task_id="U01en_demo",
        trial=2,
        model_id="openai/gpt-4.1 mini",
        steps=[TrajectoryStep(turn=1, role="assistant", content="created index.html")],
        final_artifact_path="index.html",
    )

    path = default_trace_path(tmp_path / "traces", trace)
    write_trace(path, trace)
    loaded = load_trace(path)

    assert path == tmp_path / "traces" / "U01en_demo" / "openai_gpt-4.1_mini" / "trial-002.json"
    assert loaded.task_id == trace.task_id
    assert loaded.steps[0].content == "created index.html"


def test_summarize_suite_tracks_missing_tasks() -> None:
    summaries = summarize_by_task(
        [
            Verdict(task_id="U01en_demo", trial=1, score=1.0, passed=True),
            Verdict(task_id="U01en_demo", trial=2, score=1.0, passed=True),
        ],
        required_trials=2,
    )
    suite = Suite(
        suite_id="uxui_demo",
        suite_name="UX/UI Demo",
        tasks=["U01en_demo", "U02en_missing"],
    )

    summary = summarize_suite(suite, summaries)

    assert summary.pass_k is False
    assert summary.success_rate == 1.0
    assert summary.mean_score == 1.0
    assert summary.missing_tasks == ["U02en_missing"]


def test_summaries_to_markdown_includes_suite_table() -> None:
    summaries = summarize_by_task(
        [Verdict(task_id="U01en_demo", trial=1, score=1.0, passed=True)],
        required_trials=1,
    )
    suite = Suite(suite_id="uxui_demo", suite_name="UX/UI Demo", tasks=["U01en_demo"])
    suite_summaries = summarize_by_suite([suite], summaries)

    markdown = summaries_to_markdown(summaries, suite_summaries=suite_summaries)

    assert "## Suite Summary" in markdown
    assert "| `uxui_demo` | 1/1 | yes | 1.000 | 1.000 |  |" in markdown
