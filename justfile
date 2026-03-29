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
#   just sync          — install / update all dependencies
#   just build         — zensical documentation build
#   just serve         — start zensical documentation server
#   just live          — start Zensical live-reload server (alias for serve)
#   just test          — run test suite (delegates to nox)
#   just preflight     # full CI-equivalent pipeline (delegates to nox)
#   just build-release — production build with PDF and BUILD_DATE
#   just deploy        — preflight + production build (local release check)
#   just clean         — remove generated artefacts

runner := "uv run --active"
nox_runner := "uv run nox -s"
export BUILD_DATE := `date +'%Y/%m/%d'`

# Install or update all dependency groups
sync:
    uv sync --all-groups

# Build the documentation via zensical (fast — no PDF, no social cards)
build *args:
    {{ runner }} zensical build {{ args }}

# Serve the documentation using zensical (live-reload)
serve *args:
    {{ runner }} zensical serve {{ args }}

# Alias: start the Zensical development server with hot-reload
live *args:
    {{ runner }} zensical serve {{ args }}

# Run the test suite (delegates to nox for reproducible isolation)
test *args:
    {{ nox_runner }} tests {{ args }}

# Run the full CI-equivalent pipeline (delegates to nox)
preflight:
    {{ nox_runner }} preflight

# Production build: enables PDF export and injects the current date
build-release:
    ENABLE_PDF_EXPORT=true {{ runner }} zensical build --strict

# Local release check: full preflight followed by the production build
deploy: preflight build-release

# Remove generated artefacts (.nox is kept — reuse avoids reinstalling deps)
clean:
    rm -rf site/ .pytest_cache/ coverage.xml
