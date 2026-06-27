"""Suite discovery and validation."""

from __future__ import annotations

from pathlib import Path

from .models.suite import load_suite


def iter_suite_files(suites_dir: Path):
    yield from sorted(suites_dir.glob("*.yaml"))
    yield from sorted(suites_dir.glob("*.yml"))


def validate_suites(suites_dir: Path, tasks_dir: Path) -> bool:
    ok = True
    suite_count = 0
    seen: set[str] = set()
    for suite_yaml in iter_suite_files(suites_dir):
        suite_count += 1
        try:
            suite = load_suite(suite_yaml)
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {suite_yaml.name}: {exc}")
            ok = False
            continue
        if suite.suite_id in seen:
            print(f"[FAIL] {suite.suite_id}: duplicate suite_id")
            ok = False
            continue
        seen.add(suite.suite_id)
        missing_tasks = [
            task_id for task_id in suite.tasks if not (tasks_dir / task_id / "task.yaml").exists()
        ]
        if missing_tasks:
            print(
                f"[FAIL] {suite.suite_id}: missing task(s): "
                f"{', '.join(missing_tasks)}"
            )
            ok = False
            continue
        print(f"[ok]   {suite.suite_id}  ({len(suite.tasks)} tasks)")
    if suite_count == 0:
        print(f"[FAIL] no suite yaml files found under {suites_dir}")
        ok = False
    return ok
