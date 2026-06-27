"""Config loading and validation.

Config yaml files declare `model`, `judge`, and `defaults`. Environment
variables referenced as `${VAR}` are expanded from os.environ so secrets never
sit in the repo.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

_ENV_VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _expand(value: str) -> str:
    return _ENV_VAR.sub(lambda m: os.environ.get(m.group(1), ""), value)


def _expand_tree(node):
    if isinstance(node, dict):
        return {k: _expand_tree(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_expand_tree(v) for v in node]
    if isinstance(node, str):
        return _expand(node)
    return node


class ModelConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model_id: str = ""
    context_window: int = 200_000
    extra_body: dict = Field(default_factory=dict)


class JudgeConfig(ModelConfig):
    enabled: bool = True


class Defaults(BaseModel):
    trace_dir: str = "traces"
    tasks_dir: str = "tasks"
    trials: int = 3
    parallel: int = 8


class EvalConfig(BaseModel):
    model: ModelConfig
    judge: JudgeConfig
    defaults: Defaults = Field(default_factory=Defaults)


def load_config(path: str | Path) -> EvalConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return EvalConfig.model_validate(_expand_tree(raw))
