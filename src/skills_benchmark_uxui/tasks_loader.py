"""Task discovery and validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from .graders import all_check_types
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
    return True, ""


def validate_all(tasks_dir: Path) -> bool:
    ok = True
    known_check_types = set(all_check_types())
    for task_dir, task_yaml in iter_task_dirs(tasks_dir):
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
        if not task.scoring_components:
            print(f"[FAIL] {task.task_id}: no scoring_components")
            ok = False
            continue
        unknown_checks = sorted(
            {
                component.check.get("type", "")
                for component in task.scoring_components
                if component.check.get("type", "") not in known_check_types
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
    return ok
