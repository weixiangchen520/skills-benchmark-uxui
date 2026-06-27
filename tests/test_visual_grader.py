from types import SimpleNamespace

from skills_benchmark_uxui.graders.visual_grader import visual_grader
from skills_benchmark_uxui.models.task import Task
from skills_benchmark_uxui.models.trace import Trace


class CapturingJudge:
    def __init__(self) -> None:
        self.messages = []

    def grade(self, messages):
        self.messages = messages
        return {"reason": "rendered structure supports the rubric", "score": 0.9, "pass": True}


def _ctx(tmp_path, judge):
    task = Task(
        task_id="U01en_demo",
        task_name="Demo",
        category="web",
        prompt={"text": "Build a page", "language": "en"},
        scoring_components=[
            {
                "name": "visual",
                "weight": 1.0,
                "check": {"type": "visual_grader", "description": "Good visual system"},
            }
        ],
    )
    return SimpleNamespace(
        task=task,
        trace=Trace(
            task_id=task.task_id,
            trial=1,
            model_id="test",
            final_artifact_path="index.html",
        ),
        workdir=str(tmp_path),
        judge_client=judge,
    )


def test_visual_grader_includes_render_snapshot_for_judge(tmp_path) -> None:
    (tmp_path / "index.html").write_text(
        """
<html><head><title>Harbor</title></head><body>
  <section><h1>Problem</h1><p>Operators need better forecasts.</p></section>
  <section><h2>Solution</h2><p>Harbor provides API forecasts.</p></section>
</body></html>
""".lstrip(),
        encoding="utf-8",
    )
    judge = CapturingJudge()

    passed, score, rationale = visual_grader(
        {
            "type": "visual_grader",
            "description": "Coherent layout",
            "render": {
                "use_playwright": False,
                "min_sections": 2,
                "min_headings": 2,
                "min_text_chars": 20,
            },
        },
        _ctx(tmp_path, judge),
    )

    assert passed is True
    assert score == 0.9
    assert rationale == "rendered structure supports the rubric"
    assert "Render snapshot" in judge.messages[1]["content"]
    assert '"section_count": 2' in judge.messages[1]["content"]
    assert "HTML artifact" in judge.messages[1]["content"]


def test_visual_grader_fails_render_precheck_before_judge(tmp_path) -> None:
    (tmp_path / "index.html").write_text(
        "<html><body><section><h1>Only one slide</h1></section></body></html>",
        encoding="utf-8",
    )
    judge = CapturingJudge()

    passed, score, rationale = visual_grader(
        {
            "type": "visual_grader",
            "description": "Coherent layout",
            "render": {"use_playwright": False, "min_sections": 2},
        },
        _ctx(tmp_path, judge),
    )

    assert passed is False
    assert score == 0.0
    assert "section_count 1 < required 2" in rationale
    assert judge.messages == []
