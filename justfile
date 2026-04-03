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
#   just build       — MkDocs documentation build (fast)
#   just build-prod  — MkDocs documentation build (strict — mirrors CI)
#   just serve       — start MkDocs documentation server (default: port 8000)
#   just live        — alias for serve
#   just test        — run test suite (delegates to nox)
#   just preflight   — full CI-equivalent pipeline (delegates to nox)
#   just verify      — preflight + build-prod (pre-push gate)
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

# Run the full quality pipeline (lint, typecheck, tests, reuse, security)
preflight:
    {{ nox_runner }} preflight

# Full local verification: CI-equivalent gate (single pipeline)
verify:
    {{ nox_runner }} preflight

# ─── Documentation (MkDocs) ───────────────────────────────────────────────────

# Build the documentation (fast — no strict enforcement)
build:
    NO_MKDOCS_2_WARNING=true {{ runner }} mkdocs build

# Build the documentation for production (strict — every warning is an error)
build-prod:
    NO_MKDOCS_2_WARNING=true {{ runner }} mkdocs build --strict

# Start the development server (override port: just serve 8001)
serve port="8000":
    NO_MKDOCS_2_WARNING=true {{ runner }} mkdocs serve -a localhost:{{ port }}

# Alias: start the development server
live: serve

# ─── Cleanup ──────────────────────────────────────────────────────────────────

# Remove generated artefacts (.nox is kept — reuse avoids reinstalling deps)
clean:
    rm -rf site/ dist/ .pytest_cache/ .zenzic-score.json coverage.xml
