# Zenzic Monorepo Migration Master Plan

## 1. Architectural Objective

Transition the Zenzic ecosystem into a flattened Monorepo architecture. This structure enforces the **Mirror Law (ADR-020)**, centralizes CI/CD with conservative path-based routing, and utilizes prefixed Git tags to maintain independent release lifecycles.

## 2. Target Directory Structure

```text
zenzic/ (Root)
├── core/                  # Python Core Engine
├── vscode/                # TypeScript LSP Client
├── actions/               # GitHub Action
├── docs/                  # Unified Ecosystem Documentation
├── scripts/               # Shared automation scripts
├── .github/workflows/     # Path-based CI/CD pipelines
├── justfile               # Unified task runner
├── README.md              # Ecosystem Landing Page & Quickstart
└── MIGRATION-MONOREPO.md  # This checklist
```

## 3. Execution Checklist

### PHASE 1: Core Isolation (Conservative)

- [x] Create `core/` directory.
- [x] Move `src/`, `tests/`, `pyproject.toml`, `uv.lock`, `CHANGELOG.md` into `core/`.
- [x] Update root `justfile` to execute Python commands via `cd core && ...` or `uv run --project core`.
- [x] Update existing `.github/workflows/*.yml` (Core CI): add `working-directory: core` to relevant jobs/steps. Do not alter the test logic.
- [x] **GATE:** CI passes on the `main` branch.

### PHASE 2: Ecosystem Ingestion

- [x] Create `vscode/` and `actions/` directories.
- [x] Copy the contents of `zenzic-vscode` into `vscode/` (excluding `.git`).
- [x] Copy the contents of `zenzic-action` into `actions/` (excluding `.git`).
- [x] Copy the CI workflow files from `zenzic-vscode` and `zenzic-action` into the root `.github/workflows/`. Rename them to prevent conflicts (e.g., `ci-vscode.yml`, `ci-actions.yml`).
- [x] Update the ingested workflows to use `working-directory: vscode` and `working-directory: actions`.
- [x] Update root `justfile` with recipes for `vscode` and `actions`.
- [x] **GATE:** CI passes for all three components simultaneously.

### PHASE 3: CI/CD Path-Based Routing

- [x] Add `paths: ['core/**']` trigger to Core workflows.
- [x] Add `paths: ['vscode/**']` trigger to VS Code workflows.
- [x] Add `paths: ['actions/**']` trigger to Actions workflows.
- [x] Add `paths: ['docs/**', 'README.md']` trigger to Docs deployment workflow.
- [x] **GATE:** Modifying a file in `core/` triggers *only* the Core CI.

### PHASE 4: Versioning & Tagging Strategy

- [x] Configure `bump-my-version` at the root (or within each package) to support prefixed tags: `core-vX.Y.Z`, `vscode-vX.Y.Z`, `actions-vX.Y.Z`.
- [x] Update release workflows to trigger on `tags: ['core-v*']`, etc.
- [x] **GATE:** Dry-run version bumps generate correct prefixed tags.

### PHASE 5: Information Architecture & Quickstart

- [x] Rewrite root `README.md` as the unified ecosystem landing page.
- [x] Implement the "Deterministic 3-Step Quickstart" in `README.md`.
- [x] Update `docs/` to reflect the monorepo structure.
- [x] **GATE:** `uv run zenzic check all --strict` passes with DQS 98/100.

### PHASE 6: Legacy Archival (Human Bridge)

- [ ] Add deprecation notice to legacy repos.
- [ ] Archive legacy repos on GitHub.
