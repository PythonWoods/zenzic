#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
# SPDX-License-Identifier: Apache-2.0
#
# zenzic-action-wrapper.sh — Strict execution layer for the Zenzic GitHub Action.
#
# Responsibilities:
#   1. Run `uvx zenzic check all` with the caller's parameters.
#   2. Validate SARIF JSON integrity before declaring success — a SIGKILL or
#      Python runtime abort can produce a truncated file that breaks the upload.
#   3. Write all GitHub Action outputs BEFORE any exit — Code Scanning always
#      receives findings, even when the build fails with a security incident.
#   4. Enforce the Zenzic Exit Code Contract with coherent UX:
#        0  — clean (all checks passed)
#        1  — documentation findings (broken links, orphan pages, dead refs, etc.)
#        2  — SECURITY: credential detected — credential scanner / Z201 — NEVER suppressed
#        3  — SECURITY: system path traversal — path traversal guard / Z202-203 — NEVER suppressed
#        4  — QUALITY REGRESSION: zenzic diff detected a score drop vs baseline — blocks PR merge
#
#      For exit codes 2 and 3: if no findings were parsed from the SARIF file
#      (because the breach was detected before scanning completed), findings-count
#      is forced to 1 — the security incident itself — so the output remains
#      coherent with the failing build. A caller who sees "0 findings but exit 2"
#      is an inconsistent UX we refuse to ship.
#
# Environment variables consumed (injected by action.yml):
#   ZENZIC_VERSION       Zenzic release to install ("latest" or "0.7.0", etc.)
#   ZENZIC_FORMAT        Output format: text | json | sarif
#   ZENZIC_SARIF_FILE    Path for SARIF output file (default: zenzic-results.sarif)
#   ZENZIC_STRICT        "true" → pass --strict flag (warnings become errors)
#   ZENZIC_FAIL_ON_ERROR "true" → propagate exit 1 to the workflow step

#   ZENZIC_AUDIT         "true" → pass --audit flag (bypasses all suppressions)
#   ZENZIC_DIFF_BASE     Path to a JSON baseline file for zenzic diff comparison.
#   ZENZIC_CHECK_STAMP   "true" → run 'zenzic score --check-stamp' after check all.

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
ZENZIC_VERSION="${ZENZIC_VERSION:-latest}"
ZENZIC_FORMAT="${ZENZIC_FORMAT:-sarif}"
ZENZIC_SARIF_FILE="${ZENZIC_SARIF_FILE:-zenzic-results.sarif}"
ZENZIC_STRICT="${ZENZIC_STRICT:-false}"
ZENZIC_FAIL_ON_ERROR="${ZENZIC_FAIL_ON_ERROR:-true}"

ZENZIC_AUDIT="${ZENZIC_AUDIT:-false}"
ZENZIC_DIFF_BASE="${ZENZIC_DIFF_BASE:-}"
ZENZIC_CHECK_STAMP="${ZENZIC_CHECK_STAMP:-true}"

# ── SARIF path sandbox guard (BUG-006 — Action SARIF Jailbreak) ────────────────
# The sarif-file input is an output path. Any relative traversal (../../) or
# absolute path (/) would allow a workflow to write outside the checkout
# directory. This guard is the shell-level path traversal enforcer for the action layer.
case "${ZENZIC_SARIF_FILE}" in
  /*)
    echo "::error title=Zenzic — SARIF Jailbreak::sarif-file must be a relative path inside the workspace. Absolute paths are forbidden. Got: '${ZENZIC_SARIF_FILE}'" >&2
    exit 1
    ;;
  *../*|*/..|..)
    echo "::error title=Zenzic — SARIF Jailbreak::sarif-file must not contain path traversal sequences ('..').  Got: '${ZENZIC_SARIF_FILE}'" >&2
    exit 1
    ;;
esac

# ── Package spec ──────────────────────────────────────────────────────────────
# "latest" → bare `zenzic` so uvx resolves the most recent stable release.
# Any other value is treated as an exact version pin: `zenzic==0.7.0`.
PKG="zenzic"
if [ "${ZENZIC_VERSION}" != "latest" ]; then
  PKG="zenzic==${ZENZIC_VERSION}"
fi

# ── Optional flags ────────────────────────────────────────────────────────────
STRICT_FLAG=""
if [ "${ZENZIC_STRICT}" = "true" ]; then
  STRICT_FLAG="--strict"
fi

AUDIT_FLAG=""
if [ "${ZENZIC_AUDIT}" = "true" ]; then
  AUDIT_FLAG="--audit"
fi

# ── diff-base sandbox guard ───────────────────────────────────────────────────
# diff-base is a path to a JSON file inside the workspace. Reject absolute
# paths and path traversal sequences to prevent reading files outside the checkout.
DIFF_BASE_ARGS=()
if [ -n "${ZENZIC_DIFF_BASE}" ]; then
  case "${ZENZIC_DIFF_BASE}" in
    /*)
      echo "::error title=Zenzic — diff-base Jailbreak::diff-base must be a relative path inside the workspace. Absolute paths are forbidden. Got: '${ZENZIC_DIFF_BASE}'" >&2
      exit 1
      ;;
    *../*|*/..|..)
      echo "::error title=Zenzic — diff-base Jailbreak::diff-base must not contain path traversal sequences ('..').  Got: '${ZENZIC_DIFF_BASE}'" >&2
      exit 1
      ;;
  esac
  if [ -f "${ZENZIC_DIFF_BASE}" ]; then
    DIFF_BASE_ARGS=(--base "${ZENZIC_DIFF_BASE}")
  else
    echo "::warning title=Zenzic — diff-base Not Found::diff-base '${ZENZIC_DIFF_BASE}' does not exist. Falling back to saved .zenzic-score.json snapshot." >&2
  fi
fi


# ── Extra args passthrough (Sovereign Override) ──────────────────────────────
# ZENZIC_EXTRA_ARGS is set by the caller's workflow (e.g. --exclude-url …).
# Word-split intentionally: each --exclude-url <url> pair must become separate
# argv elements.  set -f disables glob expansion so that wildcards or '?'
# characters inside URLs are never expanded against the filesystem.
set -f                                  # disable globbing (glob-safe construction)
# shellcheck disable=SC2206
EXTRA_ARGS=(${ZENZIC_EXTRA_ARGS:-})    # intentional IFS word-split
set +f                                  # restore globbing

EXIT_CODE=0
FINDINGS=0

# ── Execute ───────────────────────────────────────────────────────────────────
# Make SARIF file path absolute before changing directory,
# so it's always written relative to the workspace root.
if [ -n "${ZENZIC_SARIF_FILE}" ]; then
  ZENZIC_SARIF_FILE="$(realpath -m "${ZENZIC_SARIF_FILE}")"
fi

# Navigate to the specified working directory
cd "${INPUT_WORKING_DIRECTORY}" || exit 1

if [ "${ZENZIC_FORMAT}" = "sarif" ]; then
  # SARIF path: capture stdout to file; stderr streams to the step log.
  # `|| EXIT_CODE=$?` captures the exit code without triggering set -e.
  uvx "${PKG}" check all --format sarif ${STRICT_FLAG} --ci ${AUDIT_FLAG} "${EXTRA_ARGS[@]}" \
    > "${ZENZIC_SARIF_FILE}" \
    || EXIT_CODE=$?

  # Emit SARIF path immediately — the upload step needs it regardless of outcome.
  echo "sarif-file=${ZENZIC_SARIF_FILE}" >> "${GITHUB_OUTPUT}"

  # ── SARIF integrity check ─────────────────────────────────────────────────
  # A SIGKILL or Python runtime abort can truncate the JSON mid-write.
  # Validate before parsing so the upload step can surface an accurate warning
  # instead of a cryptic GitHub API error.
  if ! python3 -c "import json, os; json.load(open(os.environ['ZENZIC_SARIF_FILE']))" 2>/dev/null; then
    echo "::warning title=Zenzic — SARIF truncated::The file '${ZENZIC_SARIF_FILE}' is not valid JSON. The process was likely aborted before completing the write (SIGKILL or runtime crash). GitHub Code Scanning upload may fail — check the step log for the true root cause." >&2
    # FINDINGS stays 0; the broken SARIF is still handed to the upload step,
    # which will surface its own error with the precise GitHub API message.
  else
    # Parse finding count only when the SARIF is structurally valid.
    FINDINGS=$(python3 - <<PYEOF || true
import json, os
try:
    with open(os.environ["ZENZIC_SARIF_FILE"]) as f:
        data = json.load(f)
    results = data["runs"][0].get("results", [])
    print(len([r for r in results if r.get("level") != "note"]))
except Exception:
    print(0)
PYEOF
)
    FINDINGS="${FINDINGS:-0}"
  fi

  # ── Suppression CAP detection ─────────────────────────────────────────────
  # When suppression_cap_fail_hard triggers, zenzic outputs a dedicated SARIF
  # with exactly one result (ruleId: SUPPRESSION_CAP_EXCEEDED) instead of the
  # normal findings SARIF. Parse it here — no second invocation of zenzic.
  CAP_EXCEEDED="false"
  CAP_TOTAL=""
  CAP_LIMIT=""
  # Deterministic CAP detection: scan ALL results for the dedicated ruleId.
  # Using jq with select() avoids the index-0 assumption — the CAP result may
  # appear at any position in the results array.
  if [ "${EXIT_CODE}" -eq 1 ]; then
    if jq -e '.runs[].results[] | select(.ruleId == "SUPPRESSION_CAP_EXCEEDED")' \
        "${ZENZIC_SARIF_FILE}" > /dev/null 2>&1; then
      CAP_EXCEEDED="true"
      CAP_TOTAL=$(jq -r '[.runs[].results[] | select(.ruleId == "SUPPRESSION_CAP_EXCEEDED") | .properties.governance.active_suppressions] | first // "?"' \
        "${ZENZIC_SARIF_FILE}" 2>/dev/null || echo "?")
      CAP_LIMIT=$(jq -r '[.runs[].results[] | select(.ruleId == "SUPPRESSION_CAP_EXCEEDED") | .properties.governance.configured_global_cap] | first // "?"' \
        "${ZENZIC_SARIF_FILE}" 2>/dev/null || echo "?")
    fi
  fi

else
  # Non-SARIF: stream output directly to the step log; capture exit code.
  uvx "${PKG}" check all --format "${ZENZIC_FORMAT}" ${STRICT_FLAG} --ci ${AUDIT_FLAG} "${EXTRA_ARGS[@]}" \
    || EXIT_CODE=$?

  # CAP detection is SARIF-only; always false for non-SARIF formats.
  CAP_EXCEEDED="false"
  CAP_TOTAL=""
  CAP_LIMIT=""

fi

SCORE=""
DEBT_PTS="0"

# ── DQS Governance Gate: zenzic score ────────────────────────────────────────
# Evaluate fail_under and suppression_cap in CI, matching local governance.
# Run even when check all returns exit 1, so users always see the score posture.
# Skipped in audit mode and on non-quality aborts (security exits 2/3).
if [ "${ZENZIC_AUDIT}" != "true" ] && { [ "${EXIT_CODE}" -eq 0 ] || [ "${EXIT_CODE}" -eq 1 ]; }; then
  SCORE_EXIT=0
  SCORE_OUTPUT=""
  SCORE_OUTPUT=$(uvx "${PKG}" score --format json --ci 2>/dev/null) || SCORE_EXIT=$?

  if [ -n "${SCORE_OUTPUT}" ]; then
    SCORE=$(echo "${SCORE_OUTPUT}" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('score', ''))
except Exception:
    print('')
" 2>/dev/null || true)
    DEBT_PTS=$(echo "${SCORE_OUTPUT}" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('suppression_debt_pts', 0))
except Exception:
    print(0)
" 2>/dev/null || true)
    DEBT_PTS="${DEBT_PTS:-0}"
  fi

  if [ "${SCORE_EXIT}" -ne 0 ]; then
    EXIT_CODE="${SCORE_EXIT}"
  fi
fi

# ── Badge Freshness Gate: zenzic score --check-stamp ─────────────────────────
# Verify that badge_stamp_files contain the current score URL.
# Skipped in audit mode (badges are not relevant for suppression-bypassed runs).
if [ "${ZENZIC_CHECK_STAMP}" = "true" ] && [ "${ZENZIC_AUDIT}" != "true" ]; then
  STAMP_EXIT=0
  uvx "${PKG}" score --check-stamp --ci || STAMP_EXIT=$?
  if [ "${STAMP_EXIT}" -ne 0 ]; then
    echo "::error::Badge freshness check failed. Run 'zenzic score --stamp' locally and commit the result."
    EXIT_CODE="${STAMP_EXIT}"
  fi
fi

# ── Zenzic Quality Gate: zenzic diff ─────────────────────────────────────────
# Run diff to detect score regression vs the baseline. Writes score and
# suppression-debt-pts to GITHUB_OUTPUT for downstream steps.
# Only runs when format is json (score snapshot is available) or when
# diff-base is explicitly provided. Skipped in audit mode.
if [ "${ZENZIC_AUDIT}" != "true" ] && { [ "${EXIT_CODE}" -eq 0 ] || [ "${EXIT_CODE}" -eq 1 ]; }; then
  if [ "${ZENZIC_FORMAT}" = "json" ] || [ -n "${ZENZIC_DIFF_BASE}" ]; then
    DIFF_EXIT=0
    DIFF_OUTPUT=""
    DIFF_OUTPUT=$(uvx "${PKG}" diff --format json "${DIFF_BASE_ARGS[@]}" 2>/dev/null) || DIFF_EXIT=$?

    if [ -n "${DIFF_OUTPUT}" ]; then
      SCORE=$(echo "${DIFF_OUTPUT}" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('current_score', ''))
except Exception:
    print('')
" 2>/dev/null || true)
      DEBT_PTS=$(echo "${DIFF_OUTPUT}" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('suppression_debt_pts', 0))
except Exception:
    print(0)
" 2>/dev/null || true)
      DEBT_PTS="${DEBT_PTS:-0}"
    fi

  fi
fi

# ── Exit Code Contract ────────────────────────────────────────────────────────
# Security incidents (exit 2 and 3) are NEVER suppressed — not even by
# fail-on-error: "false". All GitHub Action outputs are written before exit.
#
# If FINDINGS is 0 but the exit code signals a security incident, the breach
# was detected before scanning completed (e.g. during config load). Override
# findings-count to 1 — the incident itself — to preserve output coherence.
# The ::error annotation explicitly states that checks were aborted.

if [ "${EXIT_CODE}" -eq 2 ]; then
  [ "${FINDINGS}" -eq 0 ] && FINDINGS=1
  echo "findings-count=${FINDINGS}" >> "${GITHUB_OUTPUT}"
  echo "score=${SCORE}" >> "${GITHUB_OUTPUT}"
  echo "suppression-debt-pts=${DEBT_PTS}" >> "${GITHUB_OUTPUT}"
  echo "cap-exceeded=false" >> "${GITHUB_OUTPUT}"
  echo "::error title=Zenzic Security Breach — Z201 (Exit 2)::Credential pattern or hardcoded secret detected. findings-count=${FINDINGS}. Exit 2 is non-suppressible per the Zenzic Exit Code Contract." >&2
  cat >> "${GITHUB_STEP_SUMMARY}" <<'MDEOF'
## ❌ Zenzic — Security Breach (Exit 2)

A **credential pattern or hardcoded secret** was detected in the documentation. The build has been terminated.

Exit 2 is **non-suppressible** — `fail-on-error: false` has no effect.

| | |
|---|---|
MDEOF
  printf '| **Findings** | %s |\n' "${FINDINGS}" >> "${GITHUB_STEP_SUMMARY}"
  cat >> "${GITHUB_STEP_SUMMARY}" <<'MDEOF'
| **Rule** | Z201 — Credential Scanner |
| **Action** | Remove the secret and rotate it immediately |
| **Reference** | https://zenzic.dev/docs/reference/finding-codes |
MDEOF
  exit 2
fi

if [ "${EXIT_CODE}" -eq 3 ]; then
  [ "${FINDINGS}" -eq 0 ] && FINDINGS=1
  echo "findings-count=${FINDINGS}" >> "${GITHUB_OUTPUT}"
  echo "score=${SCORE}" >> "${GITHUB_OUTPUT}"
  echo "suppression-debt-pts=${DEBT_PTS}" >> "${GITHUB_OUTPUT}"
  echo "cap-exceeded=false" >> "${GITHUB_OUTPUT}"
  echo "::error title=Zenzic Boundary Breach — Z202/Z203 (Exit 3)::Path traversal or filesystem boundary violation detected. findings-count=${FINDINGS}. Exit 3 is non-suppressible per the Zenzic Exit Code Contract." >&2
  cat >> "${GITHUB_STEP_SUMMARY}" <<'MDEOF'
## ❌ Zenzic — Boundary Breach (Exit 3)

A **path traversal or filesystem boundary violation** was detected. The scan was terminated immediately.

Exit 3 is **non-suppressible** — `fail-on-error: false` has no effect.

| | |
|---|---|
MDEOF
  printf '| **Findings** | %s |\n' "${FINDINGS}" >> "${GITHUB_STEP_SUMMARY}"
  cat >> "${GITHUB_STEP_SUMMARY}" <<'MDEOF'
| **Rules** | Z202/Z203 — Path Traversal Guard |
| **Action** | Remove the offending path reference |
| **Reference** | https://zenzic.dev/docs/reference/finding-codes |
MDEOF
  exit 3
fi

# Write all outputs for non-security exits (covers both sarif and non-sarif runs).
echo "findings-count=${FINDINGS}" >> "${GITHUB_OUTPUT}"
echo "score=${SCORE}" >> "${GITHUB_OUTPUT}"
echo "suppression-debt-pts=${DEBT_PTS}" >> "${GITHUB_OUTPUT}"
echo "cap-exceeded=${CAP_EXCEEDED:-false}" >> "${GITHUB_OUTPUT}"

# ── Job Summary for exit 1 ────────────────────────────────────────────────────
if [ "${EXIT_CODE}" -eq 1 ]; then
  if [ "${CAP_EXCEEDED}" = "true" ]; then
    echo "::error title=Zenzic — Suppression CAP Exceeded (Exit 1)::Build blocked: Suppression CAP exceeded (${CAP_TOTAL}/${CAP_LIMIT}). Remediation: https://zenzic.dev/developers/how-to/release-governance-protocol" >&2
    cat >> "${GITHUB_STEP_SUMMARY}" <<'MDEOF'
## ❌ Zenzic — Suppression CAP Exceeded (Exit 1)

The suppression debt limit has been reached. The build is blocked until suppressions are reduced below the CAP.

| | |
|---|---|
MDEOF
    printf '| **Active suppressions** | %s |\n' "${CAP_TOTAL}" >> "${GITHUB_STEP_SUMMARY}"
    printf '| **Configured CAP** | %s |\n' "${CAP_LIMIT}" >> "${GITHUB_STEP_SUMMARY}"
    cat >> "${GITHUB_STEP_SUMMARY}" <<'MDEOF'
| **Remediation** | Reduce `zenzic:ignore` comments or raise `suppression_cap` in `.zenzic.toml` |
| **Playbook** | https://zenzic.dev/developers/how-to/release-governance-protocol |
MDEOF
  else
    cat >> "${GITHUB_STEP_SUMMARY}" <<'MDEOF'
## ❌ Zenzic — Documentation Findings (Exit 1)

Documentation quality checks failed. Review the findings in the step log or the Code Scanning tab.

| | |
|---|---|
MDEOF
    printf '| **Findings** | %s |\n' "${FINDINGS}" >> "${GITHUB_STEP_SUMMARY}"
    printf '| **Score** | %s |\n' "${SCORE:-n/a}" >> "${GITHUB_STEP_SUMMARY}"
    cat >> "${GITHUB_STEP_SUMMARY}" <<'MDEOF'
| **Reference** | https://zenzic.dev/docs/reference/finding-codes |
MDEOF
  fi
fi

# Exit code 1 (documentation findings) respects the caller's fail-on-error policy.
if [ "${ZENZIC_FAIL_ON_ERROR}" = "true" ] && [ "${EXIT_CODE}" -ne 0 ]; then
  exit "${EXIT_CODE}"
fi

exit 0
