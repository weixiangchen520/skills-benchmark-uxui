"""Grader interface.

A grader is instantiated per-task (from the task's `grader.py`) and asked to
score each `scoring_components` entry declared in `task.yaml`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..models.task import Task
from ..models.trace import Trace


@dataclass
class GraderContext:
    task: Task
    trace: Trace
    workdir: str  # where the agent's artifacts live for this trial
    judge_client: Any = None  # OpenAI-compatible client configured per config.judge


class Grader(ABC):
    """Subclass this in each task's `grader.py`."""

    @abstractmethod
    def score(self, component: str, check: dict, ctx: GraderContext) -> tuple[bool, float, str]:
        """Return (passed, score 0..1, rationale) for one scoring component."""
