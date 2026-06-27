"""Task schema — what a `task.yaml` deserializes into."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

Dimension = Literal["completion", "safety", "robustness"]
Language = Literal["en", "zh"]
CheckType = Literal["llm_judge", "visual_grader", "static", "custom"]
AggregationMode = Literal["pass_k", "mean_score", "success_rate"]

_TASK_ID = re.compile(r"^U\d{2}(en|zh)_[a-z0-9_]+$")


class SourceReference(BaseModel):
    name: str
    url: str = ""
    version: str = ""
    notes: str = ""


class AggregationConfig(BaseModel):
    mode: AggregationMode = "pass_k"
    required_trials: int = 3
    pass_threshold: float = 1.0

    @field_validator("required_trials")
    @classmethod
    def _required_trials_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("required_trials must be > 0")
        return value

    @field_validator("pass_threshold")
    @classmethod
    def _threshold_must_be_in_unit_interval(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("pass_threshold must be >= 0 and <= 1")
        return value


class ScoringComponent(BaseModel):
    name: str
    weight: float
    check: dict  # {type: CheckType, description: str, ...}
    dimension: Dimension = "completion"
    threshold: float = 1.0

    @field_validator("weight")
    @classmethod
    def _weight_must_be_in_unit_interval(cls, value: float) -> float:
        if value <= 0 or value > 1:
            raise ValueError("weight must be > 0 and <= 1")
        return value

    @field_validator("check")
    @classmethod
    def _check_must_have_known_type(cls, value: dict) -> dict:
        check_type = value.get("type")
        allowed = CheckType.__args__
        if check_type not in allowed:
            raise ValueError(f"check.type must be one of {allowed}")
        return value

    @field_validator("threshold")
    @classmethod
    def _threshold_must_be_in_unit_interval(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("threshold must be >= 0 and <= 1")
        return value


class TaskEnvironment(BaseModel):
    timeout_seconds: int = 900
    max_turns: int = 25
    sandbox: str = "local"


class Task(BaseModel):
    task_id: str
    task_name: str
    version: str = "1.0"
    category: str
    difficulty: str = "medium"
    tags: list[str] = Field(default_factory=list)
    source: SourceReference | None = None
    split: str = "dev"
    language: Language = "en"
    prompt: dict  # {text, language}
    tools: list[str] = Field(default_factory=list)
    tool_endpoints: list[str] = Field(default_factory=list)
    environment: TaskEnvironment = Field(default_factory=TaskEnvironment)
    scoring_components: list[ScoringComponent]
    safety_checks: list[dict] = Field(default_factory=list)
    expected_actions: list[str] = Field(default_factory=list)
    judge_rubric: str = ""
    reference_solution: str = ""
    primary_dimensions: list[Dimension] = Field(
        default_factory=lambda: ["completion", "safety", "robustness"]
    )
    aggregation: AggregationConfig = Field(default_factory=AggregationConfig)
    primary_metrics: list[str] = Field(
        default_factory=lambda: ["pass_k", "success_rate", "mean_score"]
    )

    @field_validator("task_id")
    @classmethod
    def _task_id_must_match_convention(cls, value: str) -> str:
        if not _TASK_ID.match(value):
            raise ValueError("task_id must match U<NN><lang>_<slug>, e.g. U01en_slides_pitch")
        return value

    @property
    def total_weight(self) -> float:
        return round(sum(c.weight for c in self.scoring_components), 6)


def load_task(task_yaml: Path) -> Task:
    raw = yaml.safe_load(task_yaml.read_text(encoding="utf-8"))
    return Task.model_validate(raw)
