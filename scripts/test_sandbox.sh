#!/usr/bin/env bash
# Smoke-test that the sandbox (if enabled) can build and run a no-op command.
# Mirrors claw-eval/scripts/test_sandbox.sh — replace with a real check once
# Dockerfile.agent lands.

set -euo pipefail

echo "[test_sandbox] placeholder — implement once Dockerfile.agent exists."
echo "[test_sandbox] checking python and config parse:"
python -c "from skills_benchmark_uxui.config import load_config; \
import sys; \
print('config module imports OK')"
