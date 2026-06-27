"""Static artifact checks for deterministic task criteria."""

from __future__ import annotations

import re
from pathlib import Path

from .registry import register

_NETWORK_REF = re.compile(r"""(?i)(?:href|src)\s*=\s*["'](?:https?:)?//""")


def _artifact_path(check: dict, ctx) -> Path:
    artifact = check.get("artifact") or getattr(ctx.trace, "final_artifact_path", None) or "index.html"
    artifact_path = Path(artifact)
    if artifact_path.is_absolute():
        return artifact_path
    return Path(ctx.workdir) / artifact_path


@register("static")
def static_check(check: dict, ctx) -> tuple[bool, float, str]:
    path = _artifact_path(check, ctx)
    assertions = check.get("assertions") or ["exists"]
    failures: list[str] = []

    if "exists" in assertions and not path.exists():
        failures.append(f"{path.name} does not exist")

    text = ""
    if path.exists() and path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")

    if "self_contained_html" in assertions:
        if path.suffix.lower() not in {".html", ".htm"}:
            failures.append(f"{path.name} is not an HTML file")
        if _NETWORK_REF.search(text):
            failures.append(f"{path.name} references external network assets")

    if failures:
        return False, 0.0, "; ".join(failures)
    return True, 1.0, f"static assertions passed for {path.name}"
