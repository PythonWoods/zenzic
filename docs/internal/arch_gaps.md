<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Zenzic - Architectural Gaps & Technical Debt

> *"What is not documented, does not exist; what is documented poorly, is an ambush."*
>
> This document tracks architectural gaps and technical debt identified during development, which require resolution before specific milestones (like rc1).

---

## Target: v0.5.0rc1 (The Bastion)

### 1. Versioning Automation (Noxfile)

**Identified in:** v0.5.0a4 (`fix/sentinel-hardening`)
**Component:** `noxfile.py`
**Description:** The noxfile currently only supports `patch`, `minor`, and `major` bumps. During alpha/beta iterations, it is not possible to execute a prerelease bump directly via the automation framework (`nox -s bump -- prerelease`).
**Required Action:** The noxfile must be updated to extract and support pre-release tags (bumping `pre_l` and `pre_n`) by properly interfacing with `bump-my-version`, enabling rapid iteration of testing releases without circumventing automation.

### 2. Security Pipeline Coverage (CLI Integration)

**Identified in:** v0.5.0a4 (`fix/sentinel-hardening`)
**Component:** `zenzic/cli.py`
**Description:** The scanner and reporter now have complete mutation tests safeguarding the effectiveness of the Shield (The Sentinel's Trial). However, the silencer mutant (`findings.append(...) -> pass`) within `cli.py` is not covered by the current suite because it bypasses the CLI to interface with the proxy.
**Required Action:** An end-to-end (e2e) test that triggers the full CLI and verifies the exit with code 2 and the presence of the reporter to ensure the routing is not vulnerable to amnesia (Commit 4b or later).

---

## Resolved

### ZRT-005 — Bootstrap Paradox

**Identified in:** v0.5.0a3
**Component:** `zenzic/cli.py`, `zenzic/core/scanner.py`
**Description:** `zenzic init` crashed with a configuration error when invoked in an empty directory (no existing `zenzic.toml`). The bootstrap command incorrectly assumed a valid project context was already present before it could be created.
**Resolution:** Implemented a two-phase initialization sequence: (1) write `zenzic.toml` via a template isolated from the context resolver, (2) start the validation cycle only if the configuration file already exists. The resolver now tolerates an empty directory and delegates bootstrapping to the `init` command. Verified via Genesis Test: `zenzic init` in a completely empty directory correctly generates `zenzic.toml` with the commented Shield block visible.
**Closed in:** v0.5.0a4 (`fix/sentinel-hardening`) — commit `38be6f1`

### CI-001 — Node.js 24 / npx Non-Interactive Prompt (Cloudflare Pages)

**Identified in:** v0.5.0a4 (`fix/v050a4-infra-alignment`)
**Component:** `.github/workflows/deploy-docs.yml`
**Description:** `cloudflare/wrangler-action@v3` (latest stable) calls `npx wrangler`
without the `--yes` flag. npm 10+ on Node.js 24 GitHub Actions runners blocks
non-interactive package installation, aborting the deploy with:
`"npx canceled due to missing packages and no YES option: [wrangler@4.81.0]"`.
**Resolution:** Pre-install `wrangler@latest` globally via `npm install -g` before the
action step. npx finds the binary already in PATH and skips the interactive download
entirely. `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` added to suppress the Node.js 20
deprecation warning. Remove the pre-install step only when `wrangler-action` ships a
release that passes `--yes` to npx natively.
**Closed in:** v0.5.0a4 (`fix/v050a4-infra-alignment`)
