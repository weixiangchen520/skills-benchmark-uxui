"""Result persistence and summarization helpers."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
import re
from statistics import mean

from .models.scoring import RunSummary, SuiteSummary, Verdict, aggregate_verdicts
from .models.suite import Suite
from .models.trace import Trace

_PATH_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _path_slug(value: str) -> str:
    slug = _PATH_SAFE.sub("_", value).strip("._-")
    return slug or "unknown"


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


def default_trace_path(root: Path, trace: Trace) -> Path:
    return root / trace.task_id / _path_slug(trace.model_id) / f"trial-{trace.trial:03d}.json"


def write_trace(path: Path, trace: Trace) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(trace.model_dump_json(indent=2), encoding="utf-8")


def load_trace(path: Path) -> Trace:
    return Trace.model_validate_json(path.read_text(encoding="utf-8"))


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


def summarize_suite(suite: Suite, summaries: dict[str, RunSummary]) -> SuiteSummary:
    task_summaries = {
        task_id: summaries[task_id]
        for task_id in suite.tasks
        if task_id in summaries
    }
    missing_tasks = [task_id for task_id in suite.tasks if task_id not in summaries]
    if task_summaries:
        success_rate = round(mean(summary.success_rate for summary in task_summaries.values()), 6)
        mean_score = round(mean(summary.mean_score for summary in task_summaries.values()), 6)
    else:
        success_rate = 0.0
        mean_score = 0.0

    return SuiteSummary(
        suite_id=suite.suite_id,
        suite_name=suite.suite_name,
        tasks=len(suite.tasks),
        pass_k=not missing_tasks and all(summary.pass_k for summary in task_summaries.values()),
        success_rate=success_rate,
        mean_score=mean_score,
        missing_tasks=missing_tasks,
        task_summaries=task_summaries,
    )


def summarize_by_suite(
    suites: list[Suite],
    summaries: dict[str, RunSummary],
) -> dict[str, SuiteSummary]:
    return {
        suite.suite_id: summarize_suite(suite, summaries)
        for suite in sorted(suites, key=lambda item: item.suite_id)
    }


def summaries_to_json(
    summaries: dict[str, RunSummary],
    suite_summaries: dict[str, SuiteSummary] | None = None,
) -> str:
    task_payload = {task_id: summary.model_dump() for task_id, summary in summaries.items()}
    payload: dict[str, object] = task_payload
    if suite_summaries:
        payload = {
            "tasks": task_payload,
            "suites": {
                suite_id: summary.model_dump()
                for suite_id, summary in suite_summaries.items()
            },
        }
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def summaries_to_markdown(
    summaries: dict[str, RunSummary],
    suite_summaries: dict[str, SuiteSummary] | None = None,
) -> str:
    lines = [
        "# Benchmark Summary",
        "",
        "| Task | Trials | Pass^k | Success Rate | Mean Score |",
        "|---|---:|---:|---:|---:|",
    ]
    for task_id, summary in summaries.items():
        pass_k = "yes" if summary.pass_k else "no"
        lines.append(
            f"| `{task_id}` | {summary.trials}/{summary.required_trials} | {pass_k} | "
            f"{summary.success_rate:.3f} | {summary.mean_score:.3f} |"
        )

    if suite_summaries:
        lines.extend(
            [
                "",
                "## Suite Summary",
                "",
                "| Suite | Tasks | Pass^k | Success Rate | Mean Score | Missing Tasks |",
                "|---|---:|---:|---:|---:|---|",
            ]
        )
        for suite_id, summary in suite_summaries.items():
            pass_k = "yes" if summary.pass_k else "no"
            missing = ", ".join(summary.missing_tasks) if summary.missing_tasks else ""
            lines.append(
                f"| `{suite_id}` | {len(summary.task_summaries)}/{summary.tasks} | "
                f"{pass_k} | {summary.success_rate:.3f} | "
                f"{summary.mean_score:.3f} | {missing} |"
            )

    lines.extend(["", "## Component Pass Rates", ""])
    for task_id, summary in summaries.items():
        lines.append(f"### `{task_id}`")
        if not summary.component_pass_rates:
            lines.append("")
            lines.append("No component scores recorded.")
            lines.append("")
            continue
        lines.extend(["", "| Component | Pass Rate |", "|---|---:|"])
        for component, pass_rate in sorted(summary.component_pass_rates.items()):
            lines.append(f"| `{component}` | {pass_rate:.3f} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
