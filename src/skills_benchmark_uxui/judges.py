"""LLM judge prompt construction, client adapters, and response parsing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from .config import JudgeConfig

if TYPE_CHECKING:
    from .graders.base import GraderContext


class JudgeResult(BaseModel):
    reason: str = ""
    score: float = Field(ge=0.0, le=1.0)
    passed: bool = Field(alias="pass")

    @field_validator("reason")
    @classmethod
    def _reason_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason must not be empty")
        return value


def artifact_text(ctx: "GraderContext", max_chars: int = 60_000) -> str:
    artifact = ctx.trace.final_artifact_path or "index.html"
    path = Path(artifact)
    if not path.is_absolute():
        path = Path(ctx.workdir) / path
    if not path.exists():
        return f"[artifact missing: {path}]"
    if not path.is_file():
        return f"[artifact is not a file: {path}]"
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n[truncated]"
    return text


def build_judge_messages(check: dict, ctx: "GraderContext", artifact: str) -> list[dict[str, str]]:
    component = check.get("description", "")
    rubric = check.get("rubric") or ctx.task.judge_rubric or component
    return [
        {
            "role": "system",
            "content": (
                "You are a strict benchmark judge for UX/UI agent artifacts. "
                "Return only a JSON object with keys: reason (string), score "
                "(number from 0.0 to 1.0), and pass (boolean). Do not include "
                "markdown, hidden reasoning, or extra keys."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Task ID: {ctx.task.task_id}\n"
                f"Task prompt:\n{ctx.task.prompt.get('text', '')}\n\n"
                f"Component to grade:\n{component}\n\n"
                f"Rubric:\n{rubric}\n\n"
                "Artifact content:\n"
                f"{artifact}\n\n"
                "Grade only this component. Use score >= 0.8 for clear pass, "
                "0.5 for partial, and 0.0 for missing or unusable work."
            ),
        },
    ]


def parse_judge_response(text: str) -> JudgeResult:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        payload = json.loads(text[start : end + 1])

    if "passed" in payload and "pass" not in payload:
        payload["pass"] = payload.pop("passed")
    return JudgeResult.model_validate(payload)


class OpenAIJudgeClient:
    """Small OpenAI-compatible judge adapter used by graders."""

    def __init__(self, config: JudgeConfig):
        if not config.api_key:
            raise ValueError("judge api_key is empty")
        if not config.model_id:
            raise ValueError("judge model_id is empty")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency declared in pyproject
            raise RuntimeError("openai package is required for judge calls") from exc

        self.model_id = config.model_id
        self.extra_body = config.extra_body
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url or None)

    def grade(self, messages: list[dict[str, str]]) -> JudgeResult:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
            extra_body=self.extra_body or None,
        )
        content = response.choices[0].message.content or ""
        return parse_judge_response(content)


def create_judge_client(config: JudgeConfig) -> OpenAIJudgeClient | None:
    if not config.enabled:
        return None
    if not config.api_key or not config.model_id:
        return None
    return OpenAIJudgeClient(config)


def call_judge(judge_client: Any, messages: list[dict[str, str]]) -> JudgeResult:
    if judge_client is None:
        raise ValueError("judge_client is not configured")
    if hasattr(judge_client, "grade"):
        result = judge_client.grade(messages)
    elif callable(judge_client):
        result = judge_client(messages)
    else:
        raise TypeError("judge_client must expose grade(messages) or be callable")

    if isinstance(result, JudgeResult):
        return result
    if isinstance(result, str):
        return parse_judge_response(result)
    if isinstance(result, dict):
        if "passed" in result and "pass" not in result:
            result = {**result, "pass": result["passed"]}
        return JudgeResult.model_validate(result)
    raise TypeError(f"unsupported judge result type: {type(result).__name__}")
