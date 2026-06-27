"""Scoring primitives."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Dimension = Literal["completion", "safety", "robustness"]


class Score(BaseModel):
    component: str
    passed: bool
    score: float  # 0..1
    rationale: str = ""


class Verdict(BaseModel):
    task_id: str
    trial: int
    dimensions: dict[Dimension, bool] = Field(default_factory=dict)
    component_scores: list[Score] = Field(default_factory=list)
    passed: bool = False  # Pass^1 for this trial

    @property
    def pass3(self) -> bool:
        """Caller aggregates 3 Verdicts; this is per-trial."""
        return self.passed
