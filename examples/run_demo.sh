#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
#
# run_demo.sh — The Zenzic Philosophy Tour.
#
# Five acts that cover the full spectrum of documentation integrity:
#
#   Act 0 — MkDocs Baseline    : mkdocs-basic must pass as 1.x reference.
#   Act 1 — The Gold Standard  : i18n-standard must pass with 100/100.
#   Act 2 — The Broken Docs    : broken-docs must fail, showing every error class.
#   Act 3 — The Shield         : security_lab must block traversal and absolute links.
#   Act 4 — Single-File Target : single-file-target — audit only README.md.
#   Act 5 — Custom Dir Target  : custom-dir-target — audit content/ instead of docs/.
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

# ─── Act 0: MkDocs baseline ──────────────────────────────────────────────────

print_header "Act 0 — MkDocs baseline (mkdocs-basic)"
echo "  Expected: SUCCESS — clean MkDocs 1.6-style fixture."
echo ""

if (cd "$REPO_ROOT/examples/mkdocs-basic" && uv run zenzic check all); then
    print_result "mkdocs-basic check all" "PASS"
else
    print_result "mkdocs-basic check all" "UNEXPECTED FAILURE"
fi

# ─── Act 1: Gold Standard ─────────────────────────────────────────────────────

print_header "Act 1 — The Gold Standard (i18n-standard)"
echo "  Expected: SUCCESS — 100/100 with no errors."
echo ""

if (cd "$REPO_ROOT/examples/i18n-standard" && uv run zenzic check all --strict); then
    print_result "i18n-standard check all --strict" "PASS"
else
    print_result "i18n-standard check all --strict" "UNEXPECTED FAILURE"
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
echo "  Expected: EXIT 2 — Shield blocks credential exposure (and reports link violations)."
echo ""

if (cd "$REPO_ROOT/examples/security_lab" && uv run zenzic check all); then
    print_result "security_lab Shield" "UNEXPECTED PASS"
else
    code=$?
    if [ "$code" -eq 2 ]; then
        print_result "security_lab Shield (exit 2)" "FAIL"
    else
        print_result "security_lab Shield" "UNEXPECTED EXIT $code"
    fi
fi

# ─── Act 4: Single-File Target ────────────────────────────────────────────────

print_header "Act 4 — Single-File Target (single-file-target)"
echo "  Expected: SUCCESS — banner shows ./README.md • 1 file (1 docs, 0 assets)."
echo ""

if (cd "$REPO_ROOT/examples/single-file-target" && uv run zenzic check all README.md); then
    print_result "single-file-target check all README.md" "PASS"
else
    print_result "single-file-target check all README.md" "UNEXPECTED FAILURE"
fi

# ─── Act 5: Custom Dir Target ────────────────────────────────────────────────

print_header "Act 5 — Custom Dir Target (custom-dir-target)"
echo "  Expected: SUCCESS — banner shows ./content/ with 2 files audited."
echo ""

if (cd "$REPO_ROOT/examples/custom-dir-target" && uv run zenzic check all content/); then
    print_result "custom-dir-target check all content/" "PASS"
else
    print_result "custom-dir-target check all content/" "UNEXPECTED FAILURE"
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
echo "  Act 1 (Gold Standard)     : must be green"
echo "  Act 2 (Broken Docs)       : must be red — errors are the feature"
echo "  Act 3 (Shield)            : must be red — attacks are blocked"
echo "  Act 4 (Single-File Target): must be green — 1 file audited"
echo "  Act 5 (Custom Dir Target) : must be green — content/ audited"
echo ""
