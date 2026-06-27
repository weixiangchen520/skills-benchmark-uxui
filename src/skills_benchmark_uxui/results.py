"""Result persistence and summarization helpers."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .models.scoring import RunSummary, Verdict, aggregate_verdicts


def write_verdict(path: Path, verdict: Verdict, append: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as file:
        file.write(verdict.model_dump_json())
        file.write("\n")


def load_verdicts(path: Path) -> list[Verdict]:
    verdicts: list[Verdict] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                verdicts.append(Verdict.model_validate_json(line))
            except Exception as exc:  # noqa: BLE001
                raise ValueError(f"invalid verdict JSON on line {line_number}: {exc}") from exc
    return verdicts


def summarize_by_task(
    verdicts: list[Verdict],
    required_trials: int = 3,
) -> dict[str, RunSummary]:
    grouped: dict[str, list[Verdict]] = defaultdict(list)
    for verdict in verdicts:
        grouped[verdict.task_id].append(verdict)
    return {
        task_id: aggregate_verdicts(task_verdicts, required_trials=required_trials)
        for task_id, task_verdicts in sorted(grouped.items())
    }


def summaries_to_json(summaries: dict[str, RunSummary]) -> str:
    return json.dumps(
        {task_id: summary.model_dump() for task_id, summary in summaries.items()},
        ensure_ascii=False,
        indent=2,
        default=str,
    )
