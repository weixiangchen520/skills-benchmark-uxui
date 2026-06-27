from types import SimpleNamespace

from skills_benchmark_uxui.graders.llm_judge import llm_judge
from skills_benchmark_uxui.judges import parse_judge_response
from skills_benchmark_uxui.models.task import Task
from skills_benchmark_uxui.models.trace import Trace


class FakeJudge:
    def grade(self, messages):
        assert messages[0]["role"] == "system"
        assert "Artifact content" in messages[1]["content"]
        return {"reason": "meets the rubric", "score": 0.9, "pass": True}


def test_parse_judge_response_extracts_json() -> None:
    result = parse_judge_response(
        'Here is the result:\n{"reason": "solid", "score": 0.75, "pass": true}'
    )

    assert result.passed is True
    assert result.score == 0.75
    assert result.reason == "solid"


def test_llm_judge_uses_injected_client(tmp_path) -> None:
    (tmp_path / "index.html").write_text("<html><body>Harbor</body></html>", encoding="utf-8")
    task = Task(
        task_id="U01en_demo",
        task_name="Demo",
        category="web",
        prompt={"text": "Build a page", "language": "en"},
        scoring_components=[
            {
                "name": "quality",
                "weight": 1.0,
                "check": {"type": "llm_judge", "description": "Good page"},
            }
        ],
    )
    ctx = SimpleNamespace(
        task=task,
        trace=Trace(
            task_id=task.task_id,
            trial=1,
            model_id="test",
            final_artifact_path="index.html",
        ),
        workdir=str(tmp_path),
        judge_client=FakeJudge(),
    )

    passed, score, rationale = llm_judge(
        {"type": "llm_judge", "description": "Good page"},
        ctx,
    )

    assert passed is True
    assert score == 0.9
    assert rationale == "meets the rubric"
