from skills_benchmark_uxui.models.scoring import Verdict
from skills_benchmark_uxui.models.trace import Trace, TrajectoryStep
from skills_benchmark_uxui.results import (
    default_trace_path,
    load_trace,
    load_verdicts,
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
