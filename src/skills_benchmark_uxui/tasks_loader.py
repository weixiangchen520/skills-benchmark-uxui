"""Task discovery and validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from .graders import all_check_types
from .graders.base import Grader
from .models.task import load_task


def iter_task_dirs(tasks_dir: Path):
    for task_yaml in sorted(tasks_dir.glob("*/task.yaml")):
        yield task_yaml.parent, task_yaml


def _can_import_grader(task_dir: Path) -> tuple[bool, str]:
    grader_py = task_dir / "grader.py"
    if not grader_py.exists():
        return False, "missing grader.py"

    spec = importlib.util.spec_from_file_location(f"_task_grader_{task_dir.name}", grader_py)
    if spec is None or spec.loader is None:
        return False, "could not load grader.py"

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001
        return False, f"grader.py import failed: {exc}"

    if not hasattr(module, "grader"):
        return False, "grader.py must expose `grader`"
    grader = module.grader
    if not isinstance(grader, type) or not issubclass(grader, Grader):
        return False, "`grader` must be a Grader subclass"
    return True, ""


def validate_all(tasks_dir: Path) -> bool:
    ok = True
    known_check_types = set(all_check_types())
    task_count = 0
    for task_dir, task_yaml in iter_task_dirs(tasks_dir):
        task_count += 1
        try:
            task = load_task(task_yaml)
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {task_dir.name}: {exc}")
            ok = False
            continue
        if task.task_id != task_dir.name:
            print(f"[FAIL] {task.task_id}: task_id must match directory name {task_dir.name}")
            ok = False
            continue
        total = task.total_weight
        if abs(total - 1.0) > 1e-6:
            print(f"[FAIL] {task.task_id}: scoring weights sum to {total}, expected 1.0")
            ok = False
            continue
        component_names = [component.name for component in task.scoring_components]
        duplicate_components = sorted(
            {name for name in component_names if component_names.count(name) > 1}
        )
        if duplicate_components:
            print(
                f"[FAIL] {task.task_id}: duplicate scoring component(s): "
                f"{', '.join(duplicate_components)}"
            )
            ok = False
            continue
        if not task.scoring_components:
            print(f"[FAIL] {task.task_id}: no scoring_components")
            ok = False
            continue
        dimensions = {component.dimension for component in task.scoring_components}
        missing_dimensions = [
            dimension for dimension in task.primary_dimensions if dimension not in dimensions
        ]
        if missing_dimensions:
            print(
                f"[FAIL] {task.task_id}: primary dimension(s) without scoring components: "
                f"{', '.join(missing_dimensions)}"
            )
            ok = False
            continue
        unknown_checks = sorted(
            {
                component.check.get("type", "")
                for component in task.scoring_components
                if component.check.get("type", "") not in known_check_types
                and component.check.get("type", "") != "custom"
            }
        )
        if unknown_checks:
            print(f"[FAIL] {task.task_id}: unknown check type(s): {', '.join(unknown_checks)}")
            ok = False
            continue
        grader_ok, grader_error = _can_import_grader(task_dir)
        if not grader_ok:
            print(f"[FAIL] {task.task_id}: {grader_error}")
            ok = False
            continue
        print(f"[ok]   {task.task_id}  ({len(task.scoring_components)} components, w={total})")
    if task_count == 0:
        print(f"[FAIL] no task.yaml files found under {tasks_dir}")
        ok = False
    return ok
