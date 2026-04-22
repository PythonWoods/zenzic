#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
#
# run_demo.sh — The Zenzic Philosophy Tour.
#
# Nine acts (Acts 0–8) that cover the full spectrum of documentation integrity:
#
#   Act 0 — Linter Demo        : mkdocs-basic shows FILE_NOT_FOUND + BROKEN_ANCHOR.
#   Act 1 — The Gold Standard  : i18n-standard must pass with 100/100.
#   Act 2 — The Broken Docs    : broken-docs must fail, showing every error class.
#   Act 3 — The Shield         : security_lab must block traversal and absolute links.
#   Act 4 — Single-File Target : single-file-target — audit only README.md.
#   Act 5 — Custom Dir Target  : custom-dir-target — audit content/ instead of docs/.
#   Act 6 — Transparent Proxy  : zensical-bridge — SENTINEL banner + bridge activation.
#   Act 7 — The Flagship       : docusaurus-v3-enterprise — versioned docs + @site/ + i18n.
#   Act 8 — Minimum Viable     : standalone-markdown — MISSING_DIRECTORY_INDEX on bare .md.
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

print_header "Act 0 — Linter Demo (mkdocs-basic)"
echo "  Expected: FAILURE — FILE_NOT_FOUND (guide/index.md → ../deployment.md)"
echo "                       BROKEN_ANCHOR (api.md → guide/index.md#advanced-configuration)"
echo ""

if (cd "$REPO_ROOT/examples/mkdocs-basic" && uv run zenzic check all); then
    print_result "mkdocs-basic check all" "UNEXPECTED PASS"
else
    print_result "mkdocs-basic check all (errors are the feature)" "FAIL"
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

# ─── Act 6: Transparent Proxy ───────────────────────────────────────────────

print_header "Act 6 — Transparent Proxy (zensical-bridge)"
echo "  engine = \"zensical\" declared, NO zensical.toml present — only mkdocs.yml."
echo "  Expected: SENTINEL banner printed + SUCCESS."
echo ""

if (cd "$REPO_ROOT/examples/zensical-bridge" && uv run zenzic check all); then
    print_result "zensical-bridge check all (SENTINEL banner + pass)" "PASS"
else
    print_result "zensical-bridge check all" "UNEXPECTED FAILURE"
fi

# ─── Act 7: The Flagship ────────────────────────────────────────────────

print_header "Act 7 — The Flagship (docusaurus-v3-enterprise)"
echo "  Versioned docs (versioned_docs/version-1.0.0/) + @site/ aliases + i18n."
echo "  Expected: SUCCESS — all cross-version alias links resolve."
echo ""

if (cd "$REPO_ROOT/examples/docusaurus-v3-enterprise" && uv run zenzic check all); then
    print_result "docusaurus-v3-enterprise check all" "PASS"
else
    print_result "docusaurus-v3-enterprise check all" "UNEXPECTED FAILURE"
fi

# ─── Act 8: Minimum Viable ──────────────────────────────────────────────

print_header "Act 8 — Minimum Viable (standalone-markdown)"
echo "  No build engine. docs/deep-folder/ has no index.md."
echo "  Expected: MISSING_DIRECTORY_INDEX info finding + SUCCESS."
echo ""

if (cd "$REPO_ROOT/examples/standalone-markdown" && uv run zenzic check all --show-info); then
    print_result "standalone-markdown check all --show-info" "PASS"
else
    print_result "standalone-markdown check all --show-info" "UNEXPECTED FAILURE"
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
echo "  Act 0 (Linter Demo)         : must be red — FILE_NOT_FOUND + BROKEN_ANCHOR shown"
echo "  Act 1 (Gold Standard)       : must be green"
echo "  Act 2 (Broken Docs)         : must be red — errors are the feature"
echo "  Act 3 (Shield)              : must be red — attacks are blocked"
echo "  Act 4 (Single-File Target)  : must be green — 1 file audited"
echo "  Act 5 (Custom Dir Target)   : must be green — content/ audited"
echo "  Act 6 (Transparent Proxy)   : must be green — SENTINEL banner + bridge"
echo "  Act 7 (Flagship)            : must be green — versioned @site/ + i18n"
echo "  Act 8 (Minimum Viable)      : must be green — MISSING_DIRECTORY_INDEX fires"
echo ""
