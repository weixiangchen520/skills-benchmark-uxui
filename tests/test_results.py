from skills_benchmark_uxui.models.scoring import Verdict
from skills_benchmark_uxui.results import load_verdicts, summarize_by_task, write_verdict


def test_write_load_and_summarize_verdicts(tmp_path) -> None:
    path = tmp_path / "results" / "verdicts.jsonl"
    write_verdict(path, Verdict(task_id="U01en_demo", trial=1, score=1.0, passed=True))
    write_verdict(path, Verdict(task_id="U01en_demo", trial=2, score=0.0, passed=False))

    verdicts = load_verdicts(path)
    summaries = summarize_by_task(verdicts, required_trials=2)

    assert len(verdicts) == 2
    assert summaries["U01en_demo"].pass_k is False
    assert summaries["U01en_demo"].success_rate == 0.5
