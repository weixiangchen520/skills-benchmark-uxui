# AGENTS.md

This file orients Codex (and any contributor) to the project.

## What this is

`skills-benchmark-uxui` evaluates autonomous agents on UX/UI tasks — slide
generation, web layout, accessibility, multi-turn design clarification. It is
structured after [claw-eval](https://github.com/claw-eval/claw-eval): each task
lives in `tasks/<id>/` with a `task.yaml` (prompt, tools, scoring components,
rubric) and a `grader.py`. Agents run N=3 times; a task is "passed" only if all
trials pass (Pass^3).

## Layout

- `src/skills_benchmark_uxui/` — harness. Submodules:
  - `cli.py` — `skills-benchmark-uxui batch ...` entry point.
  - `config.py` — load/validate `config_*.yaml`.
  - `runner/` — agent loop, providers, sandbox dispatch, system prompt.
  - `graders/` — `base.py`, `registry.py`, `llm_judge.py`, `visual_grader.py`.
  - `models/` — pydantic schemas: `task.py`, `trace.py`, `scoring.py`.
- `tasks/<id>/{task.yaml,grader.py}` — one dir per task.
- `mock_services/` — optional FastAPI stub servers the agent calls.
- `scripts/` — `test_sandbox.sh`, `validate_tasks.py`.
- `config_*.yaml` — model + judge + defaults. **Never commit API keys**;
  keep them in env vars or `configs/local/` (gitignored).

## Conventions

- Python 3.11+, `uv` for envs. Package is `skills_benchmark_uxui` (underscore).
- CLI binary is `skills-benchmark-uxui` (hyphen).
- Task IDs: `U<NN><lang>_<slug>` (e.g. `U01en_slides_pitch`). `lang` is `en`/`zh`.
- Every task ships a `task.yaml` AND a `grader.py`. The grader registers itself
  via `graders.registry` and implements the components declared in `task.yaml`.
- Scoring components in `task.yaml` must each have a matching check in the
  grader; weights sum to 1.0.
- Use pydantic v2 for all data models. No hand-rolled JSON schemas.

## Commands

```bash
uv pip install -e ".[dev]"          # editable install with dev extras
ruff check src tasks                # lint
pytest                              # tests (TBD)
skills-benchmark-uxui batch --config config_general.yaml --trials 3 --parallel 8
python scripts/validate_tasks.py   # sanity-check every task.yaml
```

## Eval methodology (do not silently change)

- **Pass^3**: 3 independent trials; pass = pass all 3. Don't average scores
  across trials and call it a pass.
- **Three dimensions**: Completion, Safety, Robustness. A task's final verdict
  requires all three.
- **Graders**: `llm_judge` for open-ended quality; `visual_grader` for rendered
  output (screenshots/DOM). Default judge model is gemini-3-flash via
  OpenRouter; multi_turn judge is Codex-opus-4.6. Don't swap without a note.

## When adding a task

1. `tasks/U<NN><lang>_<slug>/` with `task.yaml` + `grader.py`.
2. Declare `scoring_components` (each: name, weight, check type, description).
  Weights sum to 1.0.
3. List `primary_dimensions` (subset of completion/safety/robustness).
4. Put large fixtures under `tasks/<id>/fixtures/` and gitignore binaries.
5. Run `python scripts/validate_tasks.py` before committing.

## Security

- API keys live in env vars (`OPENROUTER_API_KEY`, `SERP_DEV_KEY`), never in
  committed yaml. Configs reference them via `${VAR}`.
- Sandbox tasks run in a container (see `Dockerfile.agent`). Never let the
  agent escape the sandbox to the host.
