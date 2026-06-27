"""System prompt assembly for UX/UI tasks."""

from __future__ import annotations

from ..models.task import Task

_BASE = (
    "You are an autonomous agent being evaluated on a UX/UI task. Produce a "
    "concrete, shippable artifact (HTML, slides, or assets) that satisfies the "
    "user's request. Prefer self-contained, runnable output. Do not ask for "
    "clarification unless the prompt is genuinely ambiguous."
)


def build_system_prompt(task: Task) -> str:
    parts = [_BASE, "", f"# Task\n{task.prompt.get('text', '')}"]
    if task.judge_rubric:
        parts.append(f"\n# Rubric (do not game)\n{task.judge_rubric}")
    return "\n".join(parts)
