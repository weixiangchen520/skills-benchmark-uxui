from pathlib import Path

from skills_benchmark_uxui.graders.evaluate import score_trace
from skills_benchmark_uxui.models.task import load_task
from skills_benchmark_uxui.models.trace import Trace


def test_score_trace_runs_task_grader(tmp_path) -> None:
    task_dir = tmp_path / "tasks" / "U01en_static_demo"
    task_dir.mkdir(parents=True)
    (task_dir / "task.yaml").write_text(
        """
task_id: U01en_static_demo
task_name: Static demo
category: web
language: en
prompt:
  text: Build an index.html page.
  language: en
scoring_components:
  - name: runs_standalone
    weight: 1.0
    dimension: robustness
    check:
      type: static
      artifact: index.html
      assertions: [exists, self_contained_html]
primary_dimensions: [robustness]
aggregation:
  required_trials: 1
  pass_threshold: 1.0
""".lstrip(),
        encoding="utf-8",
    )
    (task_dir / "grader.py").write_text(
        """
from skills_benchmark_uxui.graders.base import Grader, GraderContext
from skills_benchmark_uxui.graders.registry import get


class DemoGrader(Grader):
    def score(self, component: str, check: dict, ctx: GraderContext):
        return get(check["type"])(check, ctx)


grader = DemoGrader
""".lstrip(),
        encoding="utf-8",
    )
    artifact_dir = tmp_path / "run"
    artifact_dir.mkdir()
    (artifact_dir / "index.html").write_text("<html><body>ok</body></html>", encoding="utf-8")

    task = load_task(task_dir / "task.yaml")
    verdict = score_trace(
        task=task,
        task_dir=task_dir,
        trace=Trace(task_id=task.task_id, trial=1, model_id="test"),
        workdir=Path(artifact_dir),
    )

    assert verdict.passed is True
    assert verdict.score == 1.0
