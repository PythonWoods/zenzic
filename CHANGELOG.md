<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

> **Development history (v0.1.0 – v0.7.1):** See the [Changelog Archive](CHANGELOG.archive.md).

## [Unreleased]

### Changed (Breaking)

- **Namespace refactor for code ownership (ADR-012, Batch 1):** Governance and
  structure findings have been renumbered to dedicated bands.
  - `Z903` → `Z405` (`UNUSED_ASSET`)
  - `Z904` → `Z406` (`NAV_CONTRACT`)
  - `Z905` → `Z601` (`BRAND_OBSOLESCENCE`)
  - `Z907` → `Z602` (`I18N_PARITY`)
  `Z9xx` now remains focused on engine/system diagnostics.

### Added

- **Stability Contract constants in `codes.py`:** Added
  `FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES`, and `PLUGIN_FORBIDDEN_EXITS`
  as explicit, immutable contract surfaces for v0.8.0.
- **Tier Model formalised in the public registry:** Core/Structure/Governance
  ownership is now explicit in code mappings and documented for migration.
- **Legacy migration map for diagnostics:** Added `LEGACY_TO_CODE` mapping so
  legacy references (`Z903`, `Z904`, `Z905`, `Z907`) can be diagnosed against
  their canonical v0.8.0 replacements.

### Added

- **`_check-hooks` DX guard:** Added hidden `_check-hooks` recipe as first dependency of
  `just verify`. Emits a warning if the pre-push Final Guard hook (`pre-commit install
  -t pre-push`) is not installed locally, without blocking the verification run.
- **`version` recipe:** `just version` prints the current project version directly from
  `bump-my-version`. Fast alternative to reading `pyproject.toml` manually.
- **`release-dry --short` flag:** `just release-dry patch --short` filters the verbose
  bump-my-version output to three essential lines: current version, new version, and
  dry-run confirmation. Default behaviour (full verbose diff) is unchanged.
- **`release-contracts` DX guard:** New recipe enforces architectural contracts on the
  justfile: mandatory presence of `version`, `release`, and `release-dry` recipes;
  `--allow-dirty` must appear only in `release-dry`, never in `release`. Wired into
  `just verify` as a structural pre-flight check that fails fast on violations.

### Changed

- **Test matrix — Boundary Testing (CI parity):** Nox `PYTHONS` updated from
  `["3.11", "3.12", "3.13"]` to `["3.10", "3.14"]`, mirroring the CI Pillar Matrix
  (Floor 3.10 / Peak 3.14). Eliminates the local-vs-remote "green divergence".
- **Fixed-version sessions pinned to Peak 3.14:** `lint`, `format`, `fmt`, `typecheck`,
  `reuse`, `security`, `mutation`, and `bump` sessions updated from `python="3.11"` to
  `python="3.14"`.
- **Mypy floor lowered to 3.10:** `[tool.mypy] python_version` changed from `"3.11"` to
  `"3.10"`, enforcing compatibility at the declared `requires-python = ">=3.10"` floor.
  The `tomllib` / `tomli` compatibility guard (`sys.version_info >= (3, 11)`) and the
  `tomli>=2.0.0; python_version < '3.11'` runtime dependency were already in place.

### Fixed

- **`Z000` added to code registry (`codes.py`):** `Z000` (UNSUPPORTED_ENGINE) was
  already documented in the `codes.py` docstring schema and in `finding-codes.mdx`,
  but was absent from `CODE_NAMES`, `CODE_DESCRIPTIONS`, and `CODE_SARIF_LEVELS`.
  Registry now complete at 34 canonical codes. The `verify-codes-parity` session
  counts Z000 as a full encyclopedia entry with `{#z000}` anchor.

---
