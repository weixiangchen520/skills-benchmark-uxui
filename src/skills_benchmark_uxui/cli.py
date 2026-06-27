"""Command-line entry point.

Mirrors claw-eval's `claw-eval batch ...` surface:

    skills-benchmark-uxui batch --config config_general.yaml \
        --sandbox --trials 3 --parallel 8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config


def _cmd_batch(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.trials is not None:
        config.defaults.trials = args.trials
    if args.parallel is not None:
        config.defaults.parallel = args.parallel
    # Runner wiring lives in runner/; this stub keeps the CLI runnable.
    print(f"[batch] config={config.model.model_id} trials={config.defaults.trials} "
          f"parallel={config.defaults.parallel} tasks_dir={config.defaults.tasks_dir}")
    if args.tasks:
        print(f"[batch] task filter={args.tasks}")
    print("[batch] runner not yet wired; see src/skills_benchmark_uxui/runner/loop.py")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    from .tasks_loader import validate_all

    ok = validate_all(Path(args.tasks_dir))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skills-benchmark-uxui")
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("batch", help="Run the benchmark against a model config")
    b.add_argument("--config", required=True, help="Path to config_*.yaml")
    b.add_argument("--sandbox", action="store_true", help="Run agents in a sandbox container")
    b.add_argument("--trials", type=int, default=None, help="Override trials (default Pass^3 = 3)")
    b.add_argument("--parallel", type=int, default=None, help="Override parallel workers")
    b.add_argument("--tasks", default=None, help="Glob / id filter for tasks")
    b.set_defaults(func=_cmd_batch)

    v = sub.add_parser("validate", help="Validate every task.yaml under tasks/")
    v.add_argument("--tasks-dir", default="tasks")
    v.set_defaults(func=_cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
