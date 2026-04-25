#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
#
# run_demo.sh — The Zenzic Philosophy Tour.
#
# Seventeen acts (Acts 0–16) across four sections:
#
#   ── OS & Environment Guardrails ──────────────────────────────────────────
#   Act  0 — Linter Demo           : mkdocs-basic — FILE_NOT_FOUND + BROKEN_ANCHOR.
#   Act  1 — The Gold Standard     : i18n-standard — 100/100 zero findings.
#   Act  2 — The Broken Docs       : broken-docs — every error class.
#   Act  3 — The Shield            : security_lab — credential exposure blocked (exit 2).
#
#   ── Structural & SEO Integrity ───────────────────────────────────────────
#   Act  4 — Single-File Target    : single-file-target — audit only README.md.
#   Act  5 — Custom Dir Target     : custom-dir-target — audit content/ at runtime.
#   Act  6 — Transparent Proxy     : zensical-bridge — SENTINEL banner + bridge.
#
#   ── Enterprise Adapters & Migration ─────────────────────────────────────
#   Act  7 — The Flagship          : docusaurus-v3-enterprise — versioned + @site/ + i18n.
#   Act  8 — Standalone Excellence : standalone-markdown — full checks, no nav contract.
#   Act  9 — MkDocs Favicon Guard  : mkdocs-z404 — Z404 for theme.favicon + theme.logo.
#   Act 10 — Zensical Logo Guard   : zensical-z404 — Z404 for project.favicon + project.logo.
#
#   ── Red/Blue Team Matrix ─────────────────────────────────────────────────
#   Act 11 — Unix Security Probe   : os/unix-security — PATH_TRAVERSAL + credential BREACH.
#   Act 12 — Windows Path Integrity: os/win-integrity — Z105 ABSOLUTE_LINK on /C:/ + /UNC/.
#   Act 13 — Link Graph Stress     : rules/z100-link-graph — circular Z102 + Z104 ×2.
#   Act 14 — Shield Extreme        : rules/z200-shield — base64/pct-enc/mixed-case BREACH.
#   Act 15 — SEO Coverage          : rules/z400-seo — Z401 ×3 + Z402 ×1.
#   Act 16 — Quality Gate          : rules/z500-quality — Z501 ×3 + Z503 ×1.
#
# Usage (from repo root):
#   bash examples/run_demo.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ─── Helpers ──────────────────────────────────────────────────────────────────

print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf  "  %s\n" "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

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

# ─── OS & Environment Guardrails ─────────────────────────────────────────────

print_section "OS & Environment Guardrails  (Acts 0–3)"

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

# ─── Structural & SEO Integrity ──────────────────────────────────────────────

print_section "Structural & SEO Integrity  (Acts 4–6)"

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

# ─── Enterprise Adapters & Migration ─────────────────────────────────────────

print_section "Enterprise Adapters & Migration  (Acts 7–10)"

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

# ─── Act 9: MkDocs Favicon Guard ─────────────────────────────────────────────

print_header "Act 9 — MkDocs Favicon Guard (mkdocs-z404)"
echo "  theme.favicon and theme.logo declared in mkdocs.yml but files are missing."
echo "  Expected: FAILURE — Z404 on both asset references."
echo ""

if (cd "$REPO_ROOT/examples/mkdocs-z404" && uv run zenzic check all); then
    print_result "mkdocs-z404 check all" "UNEXPECTED PASS"
else
    print_result "mkdocs-z404 check all (Z404 fires)" "FAIL"
fi

# ─── Act 10: Zensical Logo Guard ─────────────────────────────────────────────

print_header "Act 10 — Zensical Logo Guard (zensical-z404)"
echo "  [project].favicon and [project].logo declared in zensical.toml but files are missing."
echo "  Expected: FAILURE — Z404 on both asset references."
echo ""

if (cd "$REPO_ROOT/examples/zensical-z404" && uv run zenzic check all); then
    print_result "zensical-z404 check all" "UNEXPECTED PASS"
else
    print_result "zensical-z404 check all (Z404 fires)" "FAIL"
fi

# ─── Red/Blue Team Matrix ─────────────────────────────────────────────────────

print_section "Red/Blue Team Matrix  (Acts 11–16)"

# ─── Act 11: Unix Security Probe ─────────────────────────────────────────────

print_header "Act 11 — Unix Security Probe (os/unix-security)"
echo "  Multi-hop ../chains targeting /etc/passwd, /root/.ssh/ + credential exposure"
echo "  across tables, blockquotes, link titles, URL params, and fenced blocks."
echo "  Expected: check links → EXIT 1 (PATH_TRAVERSAL), check all → EXIT 2 (BREACH)."
echo ""

if (cd "$REPO_ROOT/examples/os/unix-security" && uv run zenzic check all); then
    print_result "os/unix-security check all" "UNEXPECTED PASS"
else
    code=$?
    if [ "$code" -eq 2 ]; then
        print_result "os/unix-security check all (exit 2 — BREACH)" "FAIL"
    else
        print_result "os/unix-security check all" "UNEXPECTED EXIT $code"
    fi
fi

# ─── Act 12: Windows Path Integrity ──────────────────────────────────────────

print_header "Act 12 — Windows Path Integrity (os/win-integrity)"
echo "  /C:/, /D:/, /UNC/server/ and file:/// links trigger Z105 ABSOLUTE_LINK."
echo "  Expected: FAILURE — Z105 on every Windows-style path."
echo ""

if (cd "$REPO_ROOT/examples/os/win-integrity" && uv run zenzic check all); then
    print_result "os/win-integrity check all" "UNEXPECTED PASS"
else
    print_result "os/win-integrity check all (Z105 fires)" "FAIL"
fi

# ─── Act 13: Link Graph Stress ───────────────────────────────────────────────

print_header "Act 13 — Link Graph Stress (rules/z100-link-graph)"
echo "  Circular broken anchors (Z102) and FILE_NOT_FOUND (Z104) across 5 nodes."
echo "  Expected: FAILURE — Z102 ×13, Z104 ×2."
echo ""

if (cd "$REPO_ROOT/examples/rules/z100-link-graph" && uv run zenzic check all); then
    print_result "rules/z100-link-graph check all" "UNEXPECTED PASS"
else
    print_result "rules/z100-link-graph check all (Z102/Z104 fires)" "FAIL"
fi

# ─── Act 14: Shield Extreme ──────────────────────────────────────────────────

print_header "Act 14 — Shield Extreme (rules/z200-shield)"
echo "  Base64-encoded, percent-encoded, and mixed-case credential obfuscation."
echo "  Expected: EXIT 2 (BREACH) — Shield normalises and detects all three techniques."
echo ""

if (cd "$REPO_ROOT/examples/rules/z200-shield" && uv run zenzic check all); then
    print_result "rules/z200-shield check all" "UNEXPECTED PASS"
else
    code=$?
    if [ "$code" -eq 2 ]; then
        print_result "rules/z200-shield check all (exit 2 — BREACH)" "FAIL"
    else
        print_result "rules/z200-shield check all" "UNEXPECTED EXIT $code"
    fi
fi

# ─── Act 15: SEO Coverage ────────────────────────────────────────────────────

print_header "Act 15 — SEO Coverage (rules/z400-seo)"
echo "  Three sections without index.md (Z401) + one orphan page (Z402)."
echo "  Expected: FAILURE — Z401 ×3, Z402 ×1."
echo ""

if (cd "$REPO_ROOT/examples/rules/z400-seo" && uv run zenzic check all); then
    print_result "rules/z400-seo check all" "UNEXPECTED PASS"
else
    print_result "rules/z400-seo check all (Z401/Z402 fires)" "FAIL"
fi

# ─── Act 16: Quality Gate ────────────────────────────────────────────────────

print_header "Act 16 — Quality Gate (rules/z500-quality)"
echo "  Stub pages (TODO, FIXME, <50 words) and a broken @include snippet."
echo "  Expected: FAILURE — Z501 ×3, Z503 ×1."
echo ""

if (cd "$REPO_ROOT/examples/rules/z500-quality" && uv run zenzic check all); then
    print_result "rules/z500-quality check all" "UNEXPECTED PASS"
else
    print_result "rules/z500-quality check all (Z501/Z503 fires)" "FAIL"
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
echo "  ── OS & Environment Guardrails ──────────────────────────────────────────"
echo "  Act  0 (Linter Demo)           : must be red — FILE_NOT_FOUND + BROKEN_ANCHOR shown"
echo "  Act  1 (Gold Standard)         : must be green"
echo "  Act  2 (Broken Docs)           : must be red — errors are the feature"
echo "  Act  3 (Shield)                : must be red (exit 2) — credential BREACH"
echo "  ── Structural & SEO Integrity ───────────────────────────────────────────"
echo "  Act  4 (Single-File Target)    : must be green — 1 file audited"
echo "  Act  5 (Custom Dir Target)     : must be green — content/ audited"
echo "  Act  6 (Transparent Proxy)     : must be green — SENTINEL banner + bridge"
echo "  ── Enterprise Adapters & Migration ──────────────────────────────────────"
echo "  Act  7 (Flagship)              : must be green — versioned @site/ + i18n"
echo "  Act  8 (Standalone Excellence) : must be green — MISSING_DIRECTORY_INDEX fires"
echo "  Act  9 (MkDocs Favicon Guard)  : must be red — Z404 for theme.favicon + theme.logo"
echo "  Act 10 (Zensical Logo Guard)   : must be red — Z404 for project.favicon + project.logo"
echo "  ── Red/Blue Team Matrix ─────────────────────────────────────────────────"
echo "  Act 11 (Unix Security Probe)   : must be red (exit 2) — PATH_TRAVERSAL + BREACH"
echo "  Act 12 (Windows Path Integrity): must be red — Z105 ABSOLUTE_LINK"
echo "  Act 13 (Link Graph Stress)     : must be red — Z102 + Z104"
echo "  Act 14 (Shield Extreme)        : must be red (exit 2) — obfuscated creds BREACH"
echo "  Act 15 (SEO Coverage)          : must be red — Z401 + Z402"
echo "  Act 16 (Quality Gate)          : must be red — Z501 + Z503"
echo ""
