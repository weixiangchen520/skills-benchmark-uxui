"""Single-trial agent loop — stub.

Wire this up next:
  1. Load task (models.task.load_task)
  2. Build system prompt (runner.system_prompt)
  3. Dispatch turns through a provider (OpenAI-compatible) until max_turns
     or the agent signals completion
  4. Persist the trace (models.trace.Trace) under config.defaults.trace_dir
"""

from __future__ import annotations

from ..models.task import Task
from ..models.trace import Trace


def run_trial(task: Task, trial: int, model_id: str) -> Trace:
    raise NotImplementedError(
        "runner.loop.run_trial is not yet implemented; "
        "see the TODO in this file."
    )
