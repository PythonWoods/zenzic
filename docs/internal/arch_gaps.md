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
