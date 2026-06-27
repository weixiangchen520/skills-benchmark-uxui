"""Visual grader — screenshot/DOM-based checks for UX/UI tasks."""

from __future__ import annotations

from ..judges import artifact_text, build_judge_messages, call_judge
from .registry import register


@register("visual_grader")
def visual_grader(check: dict, ctx) -> tuple[bool, float, str]:
    try:
        artifact = artifact_text(ctx, max_chars=int(check.get("max_artifact_chars", 60_000)))
        visual_check = {
            **check,
            "description": (
                check.get("description", "")
                + " Evaluate the rendered visual quality implied by the HTML/CSS. "
                "Penalize layout instability, unreadable typography, low contrast, "
                "missing responsive constraints, and inconsistent spacing."
            ),
        }
        result = call_judge(ctx.judge_client, build_judge_messages(visual_check, ctx, artifact))
    except Exception as exc:  # noqa: BLE001
        return False, 0.0, f"visual_grader failed: {exc}"
    return result.passed, result.score, result.reason
