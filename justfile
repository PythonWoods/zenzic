# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
#
# just — interactive developer workflow (4-Gates Standard, EPOCH 4 / v0.7.0).
#
# Single source of truth for the quality pipeline. `just verify` is the
# atomic entry-point invoked by the pre-push hook AND by GitHub Actions:
# locale ≡ remote, no drift.
#
# Nox is reserved for isolated environments (multi-version compat).
#
# Quick reference:
#   just sync        — install / update all dependency groups
#   just check       — self-lint: run Zenzic on its own documentation
#   just test        — fast inner loop (pytest -n auto, NO coverage)
#   just test-cov    — audit run (serial pytest with coverage XML)
#   just test-full   — thorough Hypothesis profile (ci, multi-version via nox)
#   just verify      — Final Guard (pre-commit + test-cov + check)
#   just clean       — remove generated artefacts

set shell := ["bash", "-c"]

runner     := "uv run --active"
nox_runner := "uv run nox -s"
# Keep BUILD_DATE deterministic across Ubuntu and Git Bash on Windows runners.
export BUILD_DATE := `date -u +'%Y/%m/%d'`

# ─── Workflow ─────────────────────────────────────────────────────────────────

# Install or update all dependency groups
sync:
    uv sync --all-groups

# Self-linting: run Zenzic on its own documentation (The Sentinel's duty).
# ZRT-010 — Sovereign Parity: Pre-Launch Guard inlined; local == CI.
# Pass extra flags directly: just check --no-external
check *args:
    #!/usr/bin/env bash
    set -euo pipefail
    # Pre-Launch Guard — remove after GA deploy when all URLs resolve
    GUARD=(
      --exclude-url "https://zenzic.dev/"
      --exclude-url "https://github.com/PythonWoods/zenzic/releases/tag/v0.7.0"
    )
    {{ runner }} zenzic check all --strict "${GUARD[@]}" {{ args }}

# Inner loop: ultra-fast, parallel, no coverage (TDD feedback).
# Pillar 3 (Pure Functions) guarantees pytest-xdist worker isolation.
# Excludes `slow` markers (e.g. ZRT-002 60s deadlock guard) — opt-in via `just test-slow`.
test *args:
    {{ runner }} pytest -n auto -m "not slow" {{ args }}

# Opt-in: run slow tests (deadlock guards, long Hypothesis runs, etc.)
test-slow *args:
    {{ runner }} pytest -m "slow" {{ args }}

# Audit: serial, deterministic, with coverage XML (pre-push gate + CI)
# Coverage threshold (fail_under=80) enforced via pyproject.toml.
test-cov *args:
    {{ runner }} pytest --cov=src/zenzic --cov-report=term-missing --cov-report=json:coverage.json {{ args }}

# Run the test suite with the thorough Hypothesis profile (ci — 500 examples)
test-full *args:
    HYPOTHESIS_PROFILE=ci {{ nox_runner }} tests {{ args }}

# ─── Quality Gates (4-Gates Standard) ─────────────────────────────────────────

# Fast linter pass: run all pre-commit hooks without the full test suite.
lint:
    uvx pre-commit run --all-files

# Final Guard: atomic verification invoked by pre-push hook + GHA.
# Sequence: pre-commit (all hooks) → test-cov (with coverage gate) → zenzic self-check.
verify:
    uvx pre-commit run --all-files
    just test-cov
    just check

# ─── Cleanup ──────────────────────────────────────────────────────────────

# Remove generated artefacts (.nox is kept — reuse avoids reinstalling deps)
clean:
    rm -rf dist/ .pytest_cache/ .hypothesis/ .zenzic-score.json coverage.json
