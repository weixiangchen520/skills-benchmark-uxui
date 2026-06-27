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
from .graders import score_trace
from .models.trace import Trace
from .models.task import load_task
from .results import load_verdicts, summaries_to_json, summarize_by_task, write_verdict


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


def _cmd_score_artifact(args: argparse.Namespace) -> int:
    task_dir = Path(args.tasks_dir) / args.task_id
    task = load_task(task_dir / "task.yaml")
    trace = Trace(
        task_id=task.task_id,
        trial=args.trial,
        model_id=args.model_id,
        final_artifact_path=args.artifact,
    )
    verdict = score_trace(
        task=task,
        task_dir=task_dir,
        trace=trace,
        workdir=Path(args.workdir),
    )
    if args.output:
        write_verdict(Path(args.output), verdict, append=args.append)
    print(verdict.model_dump_json(indent=2))
    return 0 if verdict.passed else 1


def _cmd_summarize_results(args: argparse.Namespace) -> int:
    verdicts = load_verdicts(Path(args.verdicts_jsonl))
    summaries = summarize_by_task(verdicts, required_trials=args.required_trials)
    print(summaries_to_json(summaries))
    return 0


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

    s = sub.add_parser("score-artifact", help="Score an existing artifact directory for one task")
    s.add_argument("task_id", help="Task ID, e.g. U01en_slides_pitch")
    s.add_argument("--tasks-dir", default="tasks")
    s.add_argument("--workdir", required=True, help="Directory containing the generated artifact")
    s.add_argument("--artifact", default="index.html", help="Artifact path relative to workdir")
    s.add_argument("--trial", type=int, default=1)
    s.add_argument("--model-id", default="manual")
    s.add_argument("--output", default=None, help="Optional JSONL file to write the verdict to")
    s.add_argument("--append", action="store_true", help="Append to --output instead of replacing it")
    s.set_defaults(func=_cmd_score_artifact)

    r = sub.add_parser("summarize-results", help="Summarize per-trial verdict JSONL")
    r.add_argument("verdicts_jsonl")
    r.add_argument("--required-trials", type=int, default=3)
    r.set_defaults(func=_cmd_summarize_results)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
