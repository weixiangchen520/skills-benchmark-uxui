# Skills-Benchmark-UXUI

> Trustworthy evaluation of autonomous agents on UX/UI skills.
> Pass^3 · Completion · Safety · Robustness

A benchmark that grades AI agents on real-world UX/UI tasks — slide deck
generation, landing-page layout, design-system adherence, accessibility,
responsive behavior, and more. Tasks are human-verified with fine-grained
rubrics; agents are run three times and must pass all three to earn credit.

Inspired by and structured after [claw-eval](https://github.com/claw-eval/claw-eval).

## Status

Scaffold — task set and graders are under active development. The current
harness supports YAML task validation, deterministic static artifact checks,
component-level verdicts, and Pass^k trial aggregation. See
[`docs/benchmark_design.md`](docs/benchmark_design.md) for the benchmark
mechanism notes behind the design.

## Layout

```
src/skills_benchmark_uxui/   # benchmark harness (cli, runner, graders, models)
tasks/<id>/                  # one dir per task: task.yaml + grader.py
mock_services/               # stub servers the agent talks to (optional)
scripts/                     # sandbox + validation helpers
config_*.yaml                # eval configs (model, judge, defaults)
data/                        # fixtures (downloaded; see Quick Start)
```

## Quick Start

```bash
pip install uv
uv venv --python 3.11
source .venv/bin/activate       # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

export OPENROUTER_API_KEY=sk-or-...
skills-benchmark-uxui validate
bash scripts/test_sandbox.sh
```

Run a benchmark:

```bash
skills-benchmark-uxui batch --config config_general.yaml --trials 3 --parallel 8
```

Score an existing artifact directory:

```bash
skills-benchmark-uxui score-artifact U01en_slides_pitch --workdir path/to/run
skills-benchmark-uxui score-artifact U01en_slides_pitch --workdir path/to/run --output results/verdicts.jsonl --append
skills-benchmark-uxui summarize-results results/verdicts.jsonl --required-trials 3
```

## Task categories

| Split        | Focus                                                       |
|--------------|-------------------------------------------------------------|
| `slides`     | Presentation/slide generation (content + visual design)    |
| `web`        | Landing pages, responsive layouts, design-system adherence |
| `a11y`       | Accessibility, semantics, keyboard, contrast               |
| `multi_turn` | Clarifying design intent through simulated user personas    |

## Scoring

- **Pass^3** — a task counts as passed only if the agent passes in all 3 trials.
- **Completion** — did the agent deliver the requested artifact?
- **Safety** — did it avoid harmful/unauthorized actions?
- **Robustness** — does it pass consistently across trials?

Each task declares weighted `scoring_components`; each component has a
dimension, threshold, and check type. The harness reports per-component scores,
dimension verdicts, Pass^k, success rate, and mean score.

## License

MIT.
