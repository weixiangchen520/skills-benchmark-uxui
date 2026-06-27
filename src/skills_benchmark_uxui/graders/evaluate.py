"""Task grader loading and component-level scoring."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from .base import Grader, GraderContext
from ..models.scoring import Score, Verdict
from ..models.task import Task
from ..models.trace import Trace


def load_task_grader(task_dir: Path) -> type[Grader]:
    grader_py = task_dir / "grader.py"
    if not grader_py.exists():
        raise FileNotFoundError(f"missing grader.py for task {task_dir.name}")

    spec = importlib.util.spec_from_file_location(f"_task_grader_{task_dir.name}", grader_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load grader.py for task {task_dir.name}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    grader = getattr(module, "grader", None)
    if not isinstance(grader, type) or not issubclass(grader, Grader):
        raise TypeError("grader.py must expose `grader` as a Grader subclass")
    return grader


def score_trace(
    *,
    task: Task,
    task_dir: Path,
    trace: Trace,
    workdir: Path,
    judge_client: Any = None,
) -> Verdict:
    grader_cls = load_task_grader(task_dir)
    grader = grader_cls()
    ctx = GraderContext(
        task=task,
        trace=trace,
        workdir=str(workdir),
        judge_client=judge_client,
    )
    component_scores: list[Score] = []
    for component in task.scoring_components:
        try:
            passed, raw_score, rationale = grader.score(component.name, component.check, ctx)
        except Exception as exc:  # noqa: BLE001
            passed, raw_score, rationale = False, 0.0, f"grader error: {exc}"

        score = max(0.0, min(1.0, float(raw_score)))
        component_scores.append(
            Score(
                component=component.name,
                passed=bool(passed) and score >= component.threshold,
                score=score,
                rationale=rationale,
                dimension=component.dimension,
                weight=component.weight,
                check_type=component.check.get("type", ""),
            )
        )

    return Verdict.from_scores(
        task_id=task.task_id,
        trial=trace.trial,
        component_scores=component_scores,
        required_dimensions=task.primary_dimensions,
        pass_threshold=task.aggregation.pass_threshold,
    )
