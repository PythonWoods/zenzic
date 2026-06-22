#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0

# ── Zenzic Check bootstrap ─────────────────────────────────────────
# Zenzic Check direct-invocation bootstrap.
#
# NOTE (ZRT-010 — Sovereign Parity): the canonical entry-point is
# 'just check', which inlines the Pre-Launch Guard and uses the
# _zenzic_core/ path by default.  This script exists as a low-level
# fallback for direct invocation (debugging, scripting).
#
# Path resolution order:
#   1) _zenzic_core/         (canonical — mirrors CI checkout)
#   2) $ZENZIC_PROJECT_PATH  (explicit override)
#   3) ../zenzic             (legacy sibling layout — deprecated)
#
# Virtualenv-safe: UV_NO_SYNC prevents uv from auto-syncing into
# an active .venv.
# ───────────────────────────────────────────────────────────────────

set -euo pipefail

# Prevent uv from syncing into an active .venv
export UV_NO_SYNC=1

ZENZIC_PATH=""

# 1. Canonical: _zenzic_core/ (run 'just setup-core' to populate)
if [ -d "_zenzic_core" ] && [ -f "_zenzic_core/pyproject.toml" ]; then
    ZENZIC_PATH="_zenzic_core"
fi

# 2. Explicit override
if [ -z "${ZENZIC_PATH}" ] && [ -n "${ZENZIC_PROJECT_PATH:-}" ] && [ -d "${ZENZIC_PROJECT_PATH}" ]; then
    ZENZIC_PATH="${ZENZIC_PROJECT_PATH}"
fi

# 3. Legacy sibling fallback (deprecated — use 'just setup-core' instead)
if [ -z "${ZENZIC_PATH}" ] && [ -d "../zenzic" ] && [ -f "../zenzic/pyproject.toml" ]; then
    echo "WARNING: falling back to ../zenzic — run 'just setup-core' to use _zenzic_core/" >&2
    ZENZIC_PATH="../zenzic"
fi

if [ -z "${ZENZIC_PATH}" ]; then
    echo "ERROR: zenzic core not found. Run 'just setup-core' to populate _zenzic_core/." >&2
    exit 1
fi

echo "Mode: Local Zenzic (${ZENZIC_PATH})"

uv run --project "${ZENZIC_PATH}" zenzic check all --strict "$@"
