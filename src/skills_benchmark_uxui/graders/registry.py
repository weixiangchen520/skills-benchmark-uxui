"""Registry for check-type handlers (llm_judge, visual_grader, ...).

Task graders can either implement `score()` directly (switch on component name)
or delegate to a registered check-type handler. The registry makes check types
pluggable.
"""

from __future__ import annotations

from typing import Callable

CheckHandler = Callable[[dict, "object"], tuple[bool, float, str]]

_REGISTRY: dict[str, CheckHandler] = {}


def register(check_type: str) -> Callable[[CheckHandler], CheckHandler]:
    def deco(fn: CheckHandler) -> CheckHandler:
        _REGISTRY[check_type] = fn
        return fn
    return deco


def get(check_type: str) -> CheckHandler | None:
    return _REGISTRY.get(check_type)


def all_check_types() -> list[str]:
    return sorted(_REGISTRY)
