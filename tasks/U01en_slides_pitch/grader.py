"""Grader for U01en_slides_pitch.

Delegates to registered check-type handlers (llm_judge, visual_grader, static).
If a task needs bespoke logic, override `score()` and switch on component name.
"""

from __future__ import annotations

from skills_benchmark_uxui.graders.base import Grader, GraderContext
from skills_benchmark_uxui.graders.registry import get


class PitchDeckGrader(Grader):
    def score(self, component: str, check: dict, ctx: GraderContext):
        handler = get(check.get("type", ""))
        if handler is None:
            return False, 0.0, f"unknown check type: {check.get('type')}"
        return handler(check, ctx)


grader = PitchDeckGrader
