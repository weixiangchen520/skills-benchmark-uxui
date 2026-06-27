"""LLM-judge check handler."""

from __future__ import annotations

from .registry import register


@register("llm_judge")
def llm_judge(check: dict, ctx) -> tuple[bool, float, str]:
    description = check.get("description", "")
    # TODO: call ctx.judge_client with the rubric + the agent's final artifact.
    # Placeholder so task authors can wire components before the judge lands.
    return False, 0.0, f"llm_judge not implemented for: {description}"
