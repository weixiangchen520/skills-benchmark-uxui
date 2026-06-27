"""Benchmark suite schema."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class Suite(BaseModel):
    suite_id: str
    suite_name: str
    version: str = "1.0"
    description: str = ""
    tasks: list[str]
    primary_metrics: list[str] = Field(
        default_factory=lambda: ["pass_k", "success_rate", "mean_score"]
    )

    @field_validator("tasks")
    @classmethod
    def _tasks_must_not_be_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("suite tasks must not be empty")
        return value


def load_suite(path: str | Path) -> Suite:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Suite.model_validate(raw)
