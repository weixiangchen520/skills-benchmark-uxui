# Benchmark Design Notes

This project focuses on UX/UI agent skills: artifact quality, browser/web
interaction, accessibility, design-system adherence, and robustness across
independent trials.

Research date: 2026-06-27.

## Reference Implementations Reviewed

- OpenAI Evals: template-based evals, basic match/include/fuzzy checks, and
  model-graded rubrics. Custom evals are structured as data plus registry YAML.
  Source: https://github.com/openai/evals
- EleutherAI LM Evaluation Harness: YAML task configs, explicit metrics,
  aggregation functions, task groups, few-shot configuration, validation, sample
  logging, and config-file/CLI override separation.
  Source: https://github.com/EleutherAI/lm-evaluation-harness
- HELM: standardized scenarios, unified model adapters, multi-metric evaluation
  beyond accuracy, summarization, and a result inspection UI.
  Source: https://github.com/stanford-crfm/helm
- SWE-bench: reproducible Docker-based execution, prediction files, detailed
  per-instance logs, and final resolution-rate reporting.
  Source: https://github.com/princeton-nlp/SWE-bench
- WebArena and BrowserGym: environment reset, gym-style setup/step/validate
  loops, text/browser observations, trajectories, and task-specific evaluators.
  Sources: https://github.com/web-arena-x/webarena and
  https://github.com/ServiceNow/BrowserGym
- OSWorld: computer-use tasks in real VM/desktop environments, parallel
  execution, screenshots/actions/video traces, and success-rate summaries.
  Source: https://github.com/xlang-ai/OSWorld
- MT-Bench/Chatbot Arena LLM-as-judge: single-answer grading and pairwise
  judging are useful, but judge prompts must account for position, verbosity,
  and self-enhancement biases.
  Source: https://arxiv.org/abs/2306.05685

## Adopted Mechanisms

1. Task configs stay YAML-first.
   This follows OpenAI Evals and lm-evaluation-harness. Most UX/UI tasks should
   be expressible as prompts, components, deterministic static checks, and
   model/visual judge checks before needing bespoke Python code.

2. Scoring components are first-class.
   Each component has a weight, threshold, dimension, and check type. This lets
   a slide task combine content, visual system, readability, and standalone
   execution without collapsing failure modes into one opaque score.

3. Pass^k is distinct from average score.
   A task passes only when the required independent trials all pass. We still
   report success_rate and mean_score for diagnosis, but those metrics do not
   redefine the benchmark verdict.

4. Trace and artifact scoring are separate from agent execution.
   The harness can score an existing artifact directory now. A future agent
   runner can plug in by producing the same Trace and artifact contract.

5. Deterministic checks run before expensive judges where possible.
   Static checks cover artifact existence, self-contained HTML, required text,
   and simple occurrence counts. LLM and visual judges should handle subjective
   or rendered quality only after cheap checks pass.

6. Reproducibility metadata is part of the task.
   Tasks record source, split, version, environment, aggregation, and primary
   metrics. This mirrors benchmark practices where task variants and splits must
   remain comparable across runs.

## Current Gaps

- `llm_judge` and `visual_grader` are still placeholders.
- The agent runner is not wired to provider calls or sandbox execution.
- Result persistence is not implemented beyond CLI JSON output.
- Browser/Playwright rendering checks are not implemented yet.
- No leaderboard or suite-level report generator exists yet.

## Near-Term Implementation Path

1. Add a judge prompt contract that returns strict JSON with component score,
   pass/fail, and rationale.
2. Add Playwright rendering for HTML artifacts and screenshot capture.
3. Persist per-trial traces and verdict JSONL under `traces/` and `results/`.
4. Add suite-level aggregation across tasks and model IDs.
5. Add sandbox adapters for local, Docker, and browser-backed tasks.

Part of item 3 is already present: `score-artifact --output` can write per-trial
verdict JSONL, and `summarize-results` aggregates those verdicts by task.
