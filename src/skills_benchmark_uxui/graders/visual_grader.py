"""Visual grader — screenshot/DOM-based checks for UX/UI tasks."""

from __future__ import annotations

from .registry import register


@register("visual_grader")
def visual_grader(check: dict, ctx) -> tuple[bool, float, str]:
    description = check.get("description", "")
    # TODO: render the agent's HTML/slide to an image, pass to judge with the
    # rubric, and grade visual criteria (layout, contrast, alignment, etc.).
    return False, 0.0, f"visual_grader not implemented for: {description}"
