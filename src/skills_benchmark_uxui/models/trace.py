"""Trajectory and trace models for reproducibility."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TrajectoryStep(BaseModel):
    turn: int
    role: str
    content: str = ""
    tool_call: dict | None = None
    tool_result: Any | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Trace(BaseModel):
    task_id: str
    trial: int
    model_id: str
    steps: list[TrajectoryStep] = Field(default_factory=list)
    final_artifact_path: str | None = None
    error: str | None = None
