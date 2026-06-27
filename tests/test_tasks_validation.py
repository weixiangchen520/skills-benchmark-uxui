from pathlib import Path

from skills_benchmark_uxui.suites_loader import validate_suites
from skills_benchmark_uxui.tasks_loader import validate_all


def test_repository_tasks_validate() -> None:
    assert validate_all(Path("tasks")) is True
    assert validate_suites(Path("suites"), Path("tasks")) is True
