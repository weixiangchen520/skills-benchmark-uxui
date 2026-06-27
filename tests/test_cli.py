from skills_benchmark_uxui.cli import main


def test_score_artifact_writes_trace_dir(tmp_path) -> None:
    tasks_root = tmp_path / "tasks"
    task_dir = tasks_root / "U01en_static_demo"
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

    traces_dir = tmp_path / "traces"
    code = main(
        [
            "score-artifact",
            "U01en_static_demo",
            "--tasks-dir",
            str(tasks_root),
            "--workdir",
            str(artifact_dir),
            "--model-id",
            "demo/model",
            "--trace-dir",
            str(traces_dir),
        ]
    )

    trace_path = traces_dir / "U01en_static_demo" / "demo_model" / "trial-001.json"
    assert code == 0
    assert trace_path.exists()
    assert '"final_artifact_path": "index.html"' in trace_path.read_text(encoding="utf-8")
