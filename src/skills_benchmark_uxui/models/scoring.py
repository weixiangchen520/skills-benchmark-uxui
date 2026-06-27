"""Scoring primitives."""

from __future__ import annotations

from statistics import mean
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Dimension = Literal["completion", "safety", "robustness"]


class Score(BaseModel):
    component: str
    passed: bool
    score: float  # 0..1
    rationale: str = ""
    dimension: Dimension = "completion"
    weight: float = 0.0
    check_type: str = ""

    @field_validator("score")
    @classmethod
    def _score_must_be_in_unit_interval(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("score must be >= 0 and <= 1")
        return value

    @field_validator("weight")
    @classmethod
    def _weight_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("weight must be >= 0")
        return value


class Verdict(BaseModel):
    task_id: str
    trial: int
    dimensions: dict[Dimension, bool] = Field(default_factory=dict)
    component_scores: list[Score] = Field(default_factory=list)
    score: float = 0.0
    passed: bool = False  # Pass^1 for this trial
    error: str | None = None

    @field_validator("score")
    @classmethod
    def _score_must_be_in_unit_interval(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("score must be >= 0 and <= 1")
        return value

    @property
    def pass3(self) -> bool:
        """Caller aggregates 3 Verdicts; this is per-trial."""
        return self.passed

    @classmethod
    def from_scores(
        cls,
        *,
        task_id: str,
        trial: int,
        component_scores: list[Score],
        required_dimensions: list[Dimension],
        pass_threshold: float = 1.0,
    ) -> "Verdict":
        weighted_total = sum(score.weight for score in component_scores)
        if weighted_total:
            overall_score = sum(score.score * score.weight for score in component_scores) / weighted_total
        elif component_scores:
            overall_score = mean(score.score for score in component_scores)
        else:
            overall_score = 0.0

        dimensions: dict[Dimension, bool] = {}
        for dimension in required_dimensions:
            dimension_scores = [
                score for score in component_scores if score.dimension == dimension
            ]
            dimensions[dimension] = bool(dimension_scores) and all(
                score.passed for score in dimension_scores
            )

        passed = bool(component_scores) and overall_score >= pass_threshold and all(
            dimensions.values()
        )
        return cls(
            task_id=task_id,
            trial=trial,
            dimensions=dimensions,
            component_scores=component_scores,
            score=round(overall_score, 6),
            passed=passed,
        )


class RunSummary(BaseModel):
    task_id: str
    trials: int
    required_trials: int
    pass_k: bool
    success_rate: float
    mean_score: float
    component_pass_rates: dict[str, float] = Field(default_factory=dict)
    verdicts: list[Verdict] = Field(default_factory=list)


def aggregate_verdicts(verdicts: list[Verdict], required_trials: int = 3) -> RunSummary:
    """Aggregate independent trial verdicts using Pass^k semantics."""
    if not verdicts:
        raise ValueError("cannot aggregate an empty verdict list")
    if required_trials <= 0:
        raise ValueError("required_trials must be > 0")

    task_id = verdicts[0].task_id
    if any(verdict.task_id != task_id for verdict in verdicts):
        raise ValueError("all verdicts must belong to the same task")

    considered = sorted(verdicts, key=lambda verdict: verdict.trial)[:required_trials]
    component_names = sorted(
        {score.component for verdict in verdicts for score in verdict.component_scores}
    )
    component_pass_rates: dict[str, float] = {}
    for component in component_names:
        component_scores = [
            score.passed
            for verdict in verdicts
            for score in verdict.component_scores
            if score.component == component
        ]
        component_pass_rates[component] = round(
            sum(component_scores) / len(component_scores), 6
        )

    return RunSummary(
        task_id=task_id,
        trials=len(verdicts),
        required_trials=required_trials,
        pass_k=len(considered) == required_trials and all(verdict.passed for verdict in considered),
        success_rate=round(sum(verdict.passed for verdict in verdicts) / len(verdicts), 6),
        mean_score=round(mean(verdict.score for verdict in verdicts), 6),
        component_pass_rates=component_pass_rates,
        verdicts=verdicts,
    )
