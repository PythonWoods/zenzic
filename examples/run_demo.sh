#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
#
# run_demo.sh — The Zenzic Philosophy Tour.
#
# Three acts that cover the full spectrum of documentation integrity:
#
#   Act 1 — The Gold Standard  : i18n-standard must pass with 100/100.
#   Act 2 — The Broken Docs    : broken-docs must fail, showing every error class.
#   Act 3 — The Shield         : security_lab must block traversal and absolute links.
#
# Usage (from repo root):
#   bash examples/run_demo.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ─── Helpers ──────────────────────────────────────────────────────────────────

print_header() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    printf  "║  %-60s║\n" "$1"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

print_result() {
    local label="$1" status="$2"
    if [ "$status" = "PASS" ]; then
        echo "  ✓  $label — PASS"
    elif [ "$status" = "FAIL" ]; then
        echo "  ✗  $label — FAIL (expected)"
    else
        echo "  ⚠  $label — $status"
    fi
}

# ─── Prepare build artifacts ──────────────────────────────────────────────────

print_header "Preparing build artifacts"
mkdir -p docs/assets
zip -qr docs/assets/brand-kit.zip docs/assets/brand/
echo "  brand-kit.zip ready (main repo)"

echo "  i18n-standard assets are ghost artifacts — excluded_build_artifacts handles them"

# ─── Act 1: Gold Standard ─────────────────────────────────────────────────────

print_header "Act 1 — The Gold Standard (i18n-standard)"
echo "  Expected: SUCCESS — 100/100 with no errors."
echo ""

if (cd "$REPO_ROOT/examples/i18n-standard" && uv run zenzic check links); then
    print_result "i18n-standard check links" "PASS"
else
    print_result "i18n-standard check links" "UNEXPECTED FAILURE"
fi

# ─── Act 2: Broken Docs ───────────────────────────────────────────────────────

print_header "Act 2 — The Broken Docs (broken-docs)"
echo "  Expected: FAILURE — every error class must appear in the report."
echo ""

if (cd "$REPO_ROOT/examples/broken-docs" && uv run zenzic check links); then
    print_result "broken-docs check links" "UNEXPECTED PASS"
else
    print_result "broken-docs check links" "FAIL"
fi

# ─── Act 3: The Shield ────────────────────────────────────────────────────────

print_header "Act 3 — The Shield (security_lab)"
echo "  Expected: FAILURE — path traversal and absolute link violations blocked."
echo ""

if (cd "$REPO_ROOT/examples/security_lab" && uv run zenzic check links); then
    print_result "security_lab Shield" "UNEXPECTED PASS"
else
    print_result "security_lab Shield" "FAIL"
fi

# ─── Self-audit + score snapshot ──────────────────────────────────────────────

print_header "Self-audit + Score Snapshot (main repo)"

echo "--- All checks ---"
uv run zenzic check all || true
echo ""

echo "--- Reference pipeline + Shield ---"
uv run zenzic check references || true
echo ""

echo "--- Score (saves baseline) ---"
uv run zenzic score --save
echo ""

echo "Baseline written to .zenzic-score.json"
cat .zenzic-score.json
echo ""

print_header "Demo complete"
echo "  Act 1 (Gold Standard) : must be green"
echo "  Act 2 (Broken Docs)   : must be red — errors are the feature"
echo "  Act 3 (Shield)        : must be red — attacks are blocked"
echo ""
