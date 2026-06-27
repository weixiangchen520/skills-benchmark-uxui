"""Visual grader for screenshot/DOM-based UX/UI checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..judges import artifact_text, build_judge_messages, call_judge
from ..render import RenderSnapshot, render_html_snapshot
from .registry import register


def _render_config(check: dict) -> dict[str, Any]:
    config = check.get("render") or {}
    if not isinstance(config, dict):
        return {}
    return config


def _viewport(config: dict[str, Any]) -> tuple[int, int]:
    viewport = config.get("viewport") or {}
    if not isinstance(viewport, dict):
        return 1280, 720
    return int(viewport.get("width", 1280)), int(viewport.get("height", 720))


def _optional_int(config: dict[str, Any], key: str) -> int | None:
    value = config.get(key)
    if value is None:
        return None
    return int(value)


def _render_failures(snapshot: RenderSnapshot, config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if snapshot.error and snapshot.error.startswith("artifact "):
        failures.append(snapshot.error)

    min_sections = _optional_int(config, "min_sections")
    if min_sections is not None and snapshot.section_count < min_sections:
        failures.append(f"section_count {snapshot.section_count} < required {min_sections}")

    min_headings = _optional_int(config, "min_headings")
    if min_headings is not None and snapshot.heading_count < min_headings:
        failures.append(f"heading_count {snapshot.heading_count} < required {min_headings}")

    min_text_chars = _optional_int(config, "min_text_chars")
    if min_text_chars is not None and snapshot.text_chars < min_text_chars:
        failures.append(f"text_chars {snapshot.text_chars} < required {min_text_chars}")

    if config.get("require_screenshot") and not snapshot.screenshot_path:
        failures.append("screenshot was required but not captured")

    allow_horizontal_overflow = bool(config.get("allow_horizontal_overflow", False))
    if not allow_horizontal_overflow and snapshot.dom_metrics.get("overflowing_x") is True:
        failures.append("rendered page has horizontal overflow")

    if config.get("fail_on_render_error") and snapshot.error:
        failures.append(snapshot.error)

    return failures


@register("visual_grader")
def visual_grader(check: dict, ctx) -> tuple[bool, float, str]:
    snapshot: RenderSnapshot | None = None
    try:
        config = _render_config(check)
        artifact_name = str(
            check.get("artifact")
            or config.get("artifact")
            or ctx.trace.final_artifact_path
            or "index.html"
        )
        snapshot = render_html_snapshot(
            workdir=Path(ctx.workdir),
            artifact=artifact_name,
            output_dir=Path(ctx.workdir) / ".benchmark_snapshots",
            viewport=_viewport(config),
            timeout_ms=int(config.get("timeout_ms", 5_000)),
            use_playwright=bool(config.get("use_playwright", True)),
        )
        failures = _render_failures(snapshot, config)
        if failures:
            return (
                False,
                0.0,
                "visual_grader render precheck failed: "
                + "; ".join(failures)
                + "\n"
                + snapshot.as_prompt_context(max_body_chars=1_000),
            )

        artifact = artifact_text(
            ctx,
            max_chars=int(check.get("max_artifact_chars", 60_000)),
            artifact=artifact_name,
        )
        visual_check = {
            **check,
            "description": (
                check.get("description", "")
                + " Evaluate the rendered visual quality using the render snapshot "
                "and HTML/CSS. "
                "Penalize layout instability, unreadable typography, low contrast, "
                "missing responsive constraints, and inconsistent spacing."
            ),
        }
        judged_artifact = snapshot.as_prompt_context() + "\n\nHTML artifact:\n" + artifact
        result = call_judge(
            ctx.judge_client,
            build_judge_messages(visual_check, ctx, judged_artifact),
        )
    except Exception as exc:  # noqa: BLE001
        rationale = f"visual_grader failed: {exc}"
        if snapshot is not None:
            rationale += "\n" + snapshot.as_prompt_context(max_body_chars=1_000)
        return False, 0.0, rationale
    return result.passed, result.score, result.reason
