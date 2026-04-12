# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
#
# just — interactive developer workflow.
#
# Scope: commands that require an active environment or are not suitable for
# nox isolation (bootstrapping, live servers, release builds with env vars).
# Quality-assurance pipelines (lint, typecheck, tests, reuse, security) belong
# to noxfile.py and are invoked here only via `nox -s <session>`.
#
# Quick reference:
#   just sync        — install / update all dependency groups
#   just check       — self-lint: run Zenzic on its own documentation
#   just test        — run test suite (delegates to nox)
#   just test-full   — run test suite with thorough Hypothesis profile (ci)
#   just preflight   — full CI-equivalent pipeline (delegates to nox)
#   just verify      — preflight + check (pre-push gate)
#   just clean       — remove generated artefacts

runner     := "uv run --active"
nox_runner := "uv run nox -s"
export BUILD_DATE := `date +'%Y/%m/%d'`

# ─── Workflow ─────────────────────────────────────────────────────────────────

# Install or update all dependency groups
sync:
    uv sync --all-groups

# Self-linting: run Zenzic on its own documentation (The Sentinel's duty)
check:
    {{ runner }} zenzic check all --strict

# Run the test suite (delegates to nox for reproducible isolation)
test *args:
    {{ nox_runner }} tests {{ args }}

# Run the test suite with the thorough Hypothesis profile (ci — 500 examples)
test-full *args:
    HYPOTHESIS_PROFILE=ci {{ nox_runner }} tests {{ args }}

# Run the full quality pipeline (lint, typecheck, tests, reuse, security)
preflight:
    {{ nox_runner }} preflight

# Full local verification: CI-equivalent gate (single pipeline)
# Pillar 1: Zenzic guards the source BEFORE the build renders it.
verify: check preflight

# ─── Cleanup ──────────────────────────────────────────────────────────────

# Remove generated artefacts (.nox is kept — reuse avoids reinstalling deps)
clean:
    rm -rf dist/ .pytest_cache/ .hypothesis/ .zenzic-score.json coverage.xml
