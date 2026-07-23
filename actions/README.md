<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD033 MD041 MD060 -->

<p align="center">
  <a href="https://github.com/PythonWoods/zenzic-action">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/zenzic-wordmark-action-dark.svg">
      <img alt="Zenzic / action" src="assets/zenzic-wordmark-action.svg" width="350">
    </picture>
  </a>
</p>

<p align="center">Deterministic Document Integrity Engine and SAST for Markdown/MDX graphs.</p>

<p align="center">
  <a href="https://github.com/PythonWoods/zenzic-action/actions/workflows/self-check.yml"><img alt="ci-status" src="https://img.shields.io/github/actions/workflow/status/PythonWoods/zenzic-action/self-check.yml?branch=main&label=ci&style=flat-square"></a>
  <!-- zenzic:audit-badge -->
  <img src="https://img.shields.io/badge/%F0%9F%9B%A1%EF%B8%8F_zenzic--audit-passing-22c55e?style=flat-square" alt="zenzic-audit">
  <!-- zenzic:score-badge -->
  <img src="https://img.shields.io/badge/%F0%9F%9B%A1%EF%B8%8F_zenzic--score-100_%2F_100-4f46e5?style=flat-square" alt="zenzic-score">
  <a href="https://github.com/PythonWoods/zenzic-action/releases"><img alt="action version" src="https://img.shields.io/github/v/tag/PythonWoods/zenzic-action?sort=semver&label=action&color=4f46e5&style=flat-square"></a>
  <a href="https://pypi.org/project/zenzic"><img alt="zenzic on PyPI" src="https://img.shields.io/pypi/v/zenzic?label=zenzic&color=0284c7&style=flat-square"></a>
  <a href="https://pepy.tech/project/zenzic"><img alt="Downloads" src="https://img.shields.io/pepy/dt/zenzic?color=4f46e5&label=downloads&style=flat-square"></a>
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-Apache--2.0-0d9488?style=flat-square"></a>
  <a href="https://reuse.software/"><img alt="REUSE 3.x compliant" src="https://img.shields.io/badge/REUSE-3.x%20compliant-0d9488?style=flat-square"></a>
</p>

---

Run Zenzic SAST and graph integrity analysis in CI — surfacing results directly in GitHub Code Scanning without reading logs.

**Exit code contract.** The wrapper propagates Zenzic's exit codes without remapping. Exit 1 (quality) obeys `fail-on-error`. Exit 2 (credential) and exit 3 (path traversal) terminate the job regardless of `fail-on-error: false` or `--exit-zero` — security findings are never suppressed at the enforcement boundary.

## Core Features

| Feature | Category | Description |
|---|---|---|
| **Security Scanning (SAST)** | Security | Detects hardcoded tokens (Z201) and path traversal (Z202/Z203); exits 2/3 survive `fail-on-error: false` |
| **Graph Topology Analysis** | Topology | Virtual Site Map (VSM) verifies cross-file links, orphan pages, and dead navigation graph nodes |
| **Deterministic CI/CD Enforcement** | CI/CD | Zero-DBT quality gate ensuring bit-for-bit reproducible enforcement across build environments |
| **Zero-setup install** | Execution | `uvx zenzic` — no Python toolchain required on the runner |
| **SARIF output** | Integration | Findings feed directly into GitHub Code Scanning |
| **Sovereign Audit mode** | Security | `audit: "true"` bypasses suppressions to reveal unfiltered documentation graph state |
| **PR annotations** | Feedback | Inline findings on diffs, colour-coded by severity |
| **Version pinning** | Governance | Pin to exact release for deterministic, reproducible CI gates |

## Quick Start

The minimal configuration — zero Python setup, SARIF to Code Scanning in one step:

```yaml title=".github/workflows/docs.yml"
- uses: actions/checkout@v6

- name: Run Zenzic Documentation Quality Gate
  uses: PythonWoods/zenzic-action@v2
  with:
    version: "0.23.3"
    format: sarif
    upload-sarif: "true"
  permissions:
    contents: read
    security-events: write
```

Place a `.zenzic.toml` at the root of your repository and the action picks it up automatically — no `config-file` input required. Run `zenzic init` once to scaffold a config if your docs live outside the default `docs/` folder.

For advanced configuration (Configuration Discovery, Sovereign Override, Quality Gate scoring, nightly audit), see the [Zenzic Action docs](https://zenzic.dev/docs/reference/zenzic-action).

---

## 🔍 Visual Feedback

Zenzic Action surfaces findings directly where you work. No more digging through CI logs.

<p align="center">
  <img alt="GitHub Code Scanning showing Zenzic findings" src="assets/sarif-showcase.svg?v=2" width="800">
</p>

---

## Integration Blueprints

### 1. Baseline Check (SAST & Topology Verification)

This blueprint provides static application security testing (SAST), link validation, and graph topology verification. It executes during pushes and PRs, ensuring no broken links, credential leaks, or invalid configurations enter the repository.

```yaml title=".github/workflows/docs-baseline.yml"
name: Zenzic Baseline Audit

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  baseline-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v6

      - name: Run Zenzic Baseline
        uses: PythonWoods/zenzic-action@v2
        with:
          version: "0.18.0"
          format: text
          fail-on-error: "true"
```

### 2. Security Hardening (SARIF + Upload Integration)

This blueprint runs a security-hardened gate. It executes the secret scanner (`guard-scan`) to catch exposed credentials and path traversals, then uploads the SARIF report directly to the GitHub Code Scanning Security tab.

```yaml title=".github/workflows/docs-security.yml"
name: Zenzic Hardened Quality Gate

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  security-gate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v6

      - name: Run Hardened Zenzic Audit
        uses: PythonWoods/zenzic-action@v2
        with:
          version: "0.18.0"
          format: sarif
          upload-sarif: "true"
          guard-scan: "true" # Triggers early fatal check for credentials/traversals
```

### 3. PR Governance (Inline Annotations & DQS Tracking)

This blueprint implements pull-request governance. It downloads the DQS baseline from the default branch, runs the quality gate comparison, maps issues to inline annotations, and publishes a summary of the Document Quality Score (DQS) to the workflow run.

```yaml title=".github/workflows/docs-governance.yml"
name: Zenzic PR Governance & DQS Tracking

on:
  pull_request:
    branches: [ main ]

jobs:
  pr-governance:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout PR Branch
        uses: actions/checkout@v6

      - name: Download DQS Baseline from Main
        uses: dawidd6/action-download-artifact@v6
        with:
          name: zenzic-baseline
          path: .
          search_artifacts: true
        continue-on-error: true # Safe fallback if no baseline exists yet

      - name: Run Zenzic PR Quality Gate
        id: zenzic
        uses: PythonWoods/zenzic-action@v2
        with:
          version: "0.18.0"
          format: json
          diff-base: .zenzic-score.json
          fail-on-error: "true"

      - name: Report DQS Status
        if: always()
        run: |
          echo "### Zenzic Document Quality Score (DQS) Report" >> $GITHUB_STEP_SUMMARY
          echo "- **Current DQS:** ${{ steps.zenzic.outputs.score }}/100" >> $GITHUB_STEP_SUMMARY
          echo "- **Suppression Debt:** ${{ steps.zenzic.outputs.suppression-debt-pts }} pts" >> $GITHUB_STEP_SUMMARY
          echo "- **Cap Exceeded:** ${{ steps.zenzic.outputs.cap-exceeded }}" >> $GITHUB_STEP_SUMMARY
```

---

## Branch Protection Policy (Operational)

For the `zenzic-action` repository, protect `main` and enable **Require status checks to pass before merging**.

Required checks:

- `Verify (ubuntu-latest, true)`
- `Lint PR Title`
- `Check DCO`

Operational intent:

- `Verify (ubuntu-latest, true)` is the functional integrity gate for the action runtime and wrapper behavior.
- `Lint PR Title` and `Check DCO` enforce governance and legal traceability on every PR.

Fail-closed rule:

- Every required check must run on `pull_request`.
- Do not configure branch protection with required checks that are tag-only, release-only, or schedule-only workflows.

---

## Inputs

| Input | Default | Description |
|---|---|---|
| `version` | `0.23.3` | Zenzic version to install. Pin to a specific release for reproducible CI. Set `latest` for continuous evaluation. |
| `format` | `sarif` | Output format: `text`, `json`, or `sarif`. |
| `sarif-file` | `zenzic-results.sarif` | SARIF output path (when `format: sarif`). Must be a **relative** path inside the workspace. |
| `upload-sarif` | `true` | Upload SARIF to GitHub Code Scanning. |
| `strict` | `false` | Treat warnings as errors. |
| `fail-on-error` | `true` | Fail the workflow step on findings. |
| `config-file` | *(auto)* | Optional path to a config file. Auto-discovers `.zenzic.toml` → `.github/.zenzic.toml` when omitted. |
| `audit` | `false` | Sovereign audit mode: bypass all `zenzic:ignore` comments and `per_file_ignores`. Reveals the true unfiltered documentation state. Recommended for nightly builds and security review workflows. |
| `diff-base` | *(snapshot)* | Path to a JSON baseline file for `zenzic diff`. Use an artifact from the `main` branch to block PRs that increase technical debt. Falls back to `.zenzic-score.json` when omitted. |
| `guard-scan` | `false` | Run `zenzic guard scan` as a Defense-in-Depth step **before** the main quality gate. Catches hardcoded credentials and forbidden patterns that bypassed pre-commit hooks. Security findings fail with exit 2/3 and are not governed by `fail-on-error`. |

## Outputs

| Output | Description |
|---|---|
| `sarif-file` | Path to the generated SARIF file. |
| `findings-count` | Total number of findings. |
| `score` | Documentation Quality Score (0–100). Available when `format: json` or when `diff-base` is set. |
| `suppression-debt-pts` | Technical Debt points deducted from the score due to active suppressions. `0` when no suppressions are active. |
| `cap-exceeded` | `"true"` when the suppression CAP was exceeded and blocked the build; `"false"` otherwise. |

## Advanced Workflows

### Debt Regression Blocking

Block pull requests that increase documentation debt. Save a baseline from `main` as a workflow artifact; the quality-gate job downloads it and fails if `zenzic diff` reports a score drop.

```yaml
jobs:
  baseline:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Save score baseline
        uses: PythonWoods/zenzic-action@v2
        with:
          format: json
          save: "true"
      - uses: actions/upload-artifact@v4
        with:
          name: zenzic-baseline
          path: .zenzic-score.json

  quality-gate:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: zenzic-baseline
      - name: Block debt regression
        uses: PythonWoods/zenzic-action@v2
        with:
          format: json
          diff-base: .zenzic-score.json
```

### Sovereign Nightly Audit

Run a full unfiltered audit nightly to reveal the true documentation state — bypassing all `zenzic:ignore` comments and `per_file_ignores`. Findings that are suppressed in day-to-day CI are visible here.

```yaml
on:
  schedule:
    - cron: "0 3 * * *"   # 03:00 UTC daily

jobs:
  sovereign-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Sovereign audit (no suppressions)
        uses: PythonWoods/zenzic-action@v2
        with:
          audit: "true"
          format: sarif
          upload-sarif: "true"
```

### Using Action Outputs

Capture `score`, `suppression-debt-pts`, and `cap-exceeded` from the action for conditional logic or downstream reporting.

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Zenzic quality gate
    id: zenzic
    uses: PythonWoods/zenzic-action@v2
    with:
      format: json
      fail-on-error: "false"

  - name: Report score
    run: |
      echo "Score: ${{ steps.zenzic.outputs.score }}/100"
      echo "Suppression debt: ${{ steps.zenzic.outputs.suppression-debt-pts }} pts"

  - name: Fail if suppression CAP exceeded
    if: steps.zenzic.outputs.cap-exceeded == 'true'
    run: |
      echo "::error::Suppression CAP exceeded — build blocked."
      exit 1
```

---

## Exit Codes

| Code | Meaning | Suppressible? |
|:---:|---|:---:|
| `0` | All checks passed | — |
| `1` | Documentation findings (broken links, orphans, suppression CAP) | Yes (`fail-on-error: "false"`) |
| **`2`** | **Credential detected (Z201)** | **Never** |
| **`3`** | **Path traversal detected (Z202/Z203)** | **Never** |

---

For advanced governance (Scoring & Debt, Sovereign Audit, Quality Gate PR blocking), see the
[Zenzic Action docs](https://zenzic.dev/docs/reference/zenzic-action).

For security architecture internals (exit code contract, Root-First discovery, SARIF integrity guard),
see the [Engineering Ledger](https://zenzic.dev/developers/explanation/adr-vault).

## License

Apache-2.0 — see [LICENSE](LICENSE).
