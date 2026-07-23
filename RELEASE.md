<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Release Procedure — Zenzic Ecosystem

> **[MAINTAINER SOP]** *This document contains the Standard Operating Procedures for maintaining and cutting releases for all components in the Zenzic monorepo: Core Engine (`core/`), VS Code Extension (`vscode/`), and GitHub Action (`actions/`).*

---

## 1. Zenzic Core Engine (`core/`)

### Core Release Metadata

| Field | Value |
| :--- | :--- |
| **Core Version** | `v0.23.1` |
| **Codename** | Magnetite |
| **Date** | 2026-07-22 |
| **Status** | Stable |

### Core Release Checklist

Before tagging, every item must be green:

- [ ] `just verify` — exits 0 (pre-commit hooks, pytest, `zenzic check all --strict`)
- [ ] `core/pyproject.toml` version matches the tag (`0.23.1`)
- [ ] `CITATION.cff` version and date updated
- [ ] `core/CHANGELOG.md` — `[Unreleased]` section moved to the new version heading
- [ ] `SECURITY.md` support table updated

### Core Build & Tag Commands

```bash
# 1. Bump Core version (updates pyproject.toml, CHANGELOG.md, CITATION.cff, and RELEASE.md)
cd core && uv run bump-my-version bump patch

# 2. Tag Core release
git tag -s -m "Release core-v0.23.1" core-v0.23.1
git push origin core-v0.23.1
```

---

## 2. Zenzic VS Code Extension (`vscode/`)

### VS Code Release Metadata

| Field | Value |
| :--- | :--- |
| **Extension Version** | `0.23.7` |
| **Pinned Core** | `zenzic>=0.23.1` |
| **Date** | 2026-07-22 |

### VS Code Release Checklist

- [ ] `just vscode-lint` — exits 0
- [ ] `just vscode-build` — compiles extension bundle and packages `.vsix` artifact cleanly
- [ ] `vscode/CHANGELOG.md` — updated with new release notes
- [ ] `vscode/package.json` — lockfile synced (`npm ci`)

### VS Code Build & Tag Commands

```bash
# 1. Bump VS Code extension version
cd vscode && uvx bump-my-version bump patch

# 2. Tag VS Code release
git tag -s -m "Release vscode-v0.23.7" vscode-v0.23.7
git push origin vscode-v0.23.7
```

---

## 3. Zenzic GitHub Action (`actions/`)

### Action Release Metadata

| Field | Value |
| :--- | :--- |
| **Action Version** | `v2.9.1` |
| **Date** | 2026-07-22 |
| **Status** | Stable |

### Action Release Checklist

- [ ] `just action-verify` — exits 0
- [ ] `actions/action.yml` — default pin updated to latest Zenzic core version
- [ ] `actions/package.json` version bumped to `2.9.1`

### Action Build & Tag Commands

```bash
# 1. Bump Action version
cd actions && uvx bump-my-version bump patch

# 2. Tag Action release
git tag -s -m "Release actions-v2.9.1" actions-v2.9.1
git push origin actions-v2.9.1

# 3. Move floating v2 tag to new release
git tag -fa v2 actions-v2.9.1^{} -m "release(action): move v2 floating tag to actions-v2.9.1"
git push origin v2 --force
```

---

## Ecosystem Tagging Reference Matrix

| Component | Target Directory | Prefixed Tag Format | GHA Workflow |
| :--- | :--- | :--- | :--- |
| **Core Engine** | `core/` | `core-vX.Y.Z` | `.github/workflows/release.yml` |
| **VS Code Extension** | `vscode/` | `vscode-vX.Y.Z` | `.github/workflows/release-vscode.yml` |
| **GitHub Action** | `actions/` | `actions-vX.Y.Z` | `.github/workflows/release-actions.yml` |
