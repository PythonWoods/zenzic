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
#   just sync          — install / update all dependency groups
#   just check         — self-lint: run Zenzic on its own documentation
#   just build         — MkDocs documentation build (fast, strict)
#   just serve         — start MkDocs documentation server (live-reload)
#   just live          — alias for serve
#   just test          — run test suite (delegates to nox)
#   just preflight     — full CI-equivalent pipeline (delegates to nox)
#   just build-release — production build with BUILD_DATE
#   just deploy        — preflight + production build (local release check)
#   just clean         — remove generated artefacts

runner := "uv run --active"
nox_runner := "uv run nox -s"
export BUILD_DATE := `date +'%Y/%m/%d'`

# Install or update all dependency groups
sync:
    uv sync --all-groups

# Self-linting: run Zenzic on its own documentation (The Sentinel's duty)
check:
    {{ runner }} zenzic check all --strict

# Build the documentation via MkDocs (fast — no PDF, no social cards)
build *args:
    {{ runner }} mkdocs build --strict {{ args }}

# Serve the documentation using MkDocs (live-reload)
serve *args:
    {{ runner }} mkdocs serve {{ args }}

# Alias: start the MkDocs development server with hot-reload
live: serve

# Run the test suite (delegates to nox for reproducible isolation)
test *args:
    {{ nox_runner }} tests {{ args }}

# Run the full CI-equivalent pipeline (delegates to nox)
preflight:
    {{ nox_runner }} preflight

# Production build: injects the current date
build-release:
    {{ runner }} mkdocs build --strict

# Local release check: full preflight followed by the production build
deploy: preflight build-release

# Remove generated artefacts (.nox is kept — reuse avoids reinstalling deps)
clean:
    rm -rf site/ dist/ .pytest_cache/ .zenzic-score.json coverage.xml
