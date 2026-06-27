"""Validate every task.yaml under tasks/."""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from skills_benchmark_uxui.tasks_loader import validate_all


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate task.yaml and grader.py files.")
    parser.add_argument(
        "--tasks-dir",
        default=Path(__file__).resolve().parent.parent / "tasks",
        type=Path,
        help="Directory containing task subdirectories.",
    )
    args = parser.parse_args()
    tasks_dir = args.tasks_dir
    return 0 if validate_all(tasks_dir) else 1


if __name__ == "__main__":
    sys.exit(main())
