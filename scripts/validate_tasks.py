"""Validate every task.yaml under tasks/."""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from skills_benchmark_uxui.tasks_loader import validate_all
from skills_benchmark_uxui.suites_loader import validate_suites


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate task.yaml and grader.py files.")
    parser.add_argument(
        "--tasks-dir",
        default=Path(__file__).resolve().parent.parent / "tasks",
        type=Path,
        help="Directory containing task subdirectories.",
    )
    parser.add_argument(
        "--suites-dir",
        default=Path(__file__).resolve().parent.parent / "suites",
        type=Path,
        help="Directory containing suite yaml files.",
    )
    args = parser.parse_args()
    tasks_ok = validate_all(args.tasks_dir)
    suites_ok = validate_suites(args.suites_dir, args.tasks_dir)
    return 0 if tasks_ok and suites_ok else 1


if __name__ == "__main__":
    sys.exit(main())
