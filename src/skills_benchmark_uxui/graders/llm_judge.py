"""LLM-judge check handler."""

from __future__ import annotations

from ..judges import artifact_text, build_judge_messages, call_judge
from .registry import register


@register("llm_judge")
def llm_judge(check: dict, ctx) -> tuple[bool, float, str]:
    try:
        artifact = artifact_text(ctx, max_chars=int(check.get("max_artifact_chars", 60_000)))
        result = call_judge(ctx.judge_client, build_judge_messages(check, ctx, artifact))
    except Exception as exc:  # noqa: BLE001
        return False, 0.0, f"llm_judge failed: {exc}"
    return result.passed, result.score, result.reason
