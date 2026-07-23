<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to zenzic-action are documented in this file. The project adheres to Semantic Versioning. Major releases represent breaking changes to inputs/outputs, minor releases introduce new options or core package bumps, and patch releases address bug fixes. Format follows Keep a Changelog.

---

## [Unreleased]

## [2.9.1] - 2026-07-22

### Changed

- **Dependencies**: Strictly pinned Zenzic Core dependency to version `0.23.1` (`zenzic == 0.23.1` @ SHA `67b4ee3632681065b304891ef388b99010d999bf`), deploying LSP `codeDescription` links and `[{code}]` diagnostic message prefixing per ADR-089 / ADR-090.

## [2.9.0] - 2026-07-18

### Changed

- **Dependencies**: Pinned Zenzic core dependency to version `0.23.0` (introduces `ZenzicDiagnostic` strict typing, incremental VSM validation via `IncrementalAnalysisEngine`, `VirtualBufferOverlay` reverse index, and ADR-075 Radical Unawareness compliance in the Language Server).

## [2.8.3] - 2026-07-14

### Changed

- **Dependencies**: Pinned Zenzic core dependency to version `0.22.3` (restoring 100% diagnostic parity and URP strict ordering).

## [2.8.2] - 2026-07-14

## [2.8.1] - 2026-07-14

## [2.8.0] - 2026-07-12

### Added

- **Core Update**: Pinned Zenzic core dependency to version `0.22.0` (introduces Real-Time Virtual Site Map (VSM) integration and O(1) incremental patching to the Language Server).

## [2.7.1] - 2026-07-11

## [2.7.0] - 2026-07-11

## [2.6.2] - 2026-07-05

### Changed

- **Dependencies**: Pinned Zenzic core dependency to version `0.20.3` (eradicates Z602 bilingual parity rules/fixtures, and aligns with English-Only documentation governance).

## [2.6.1] - 2026-07-04

### Changed

- **Dependencies**: Pinned Zenzic core dependency to version `0.20.1` (restores slate-based dark mode and resolves Z603 Dead Suppression paradox).

## [2.6.0] - 2026-07-04

### Added

- **Core Update**: Bumped Zenzic core dependency to `>=0.20.0` (introduces Custom Rules API v2, deterministic visitation sandbox, and auto-fix expansion for Z121 and Z603).

### Changed

- **Dependencies**: Pinned Zenzic core to `0.20.0`.

## [2.5.2] - 2026-07-04

### 🔒 Security Advisory

- **Core Update**: Bumped Zenzic core dependency to `>=0.19.6` to mitigate the DQS Evasion (leading space bypass), TOML Bomb crash, and duplicate suppression consumption vulnerabilities.

### Changed

- **Dependencies**: Pinned Zenzic core to `0.19.6`.
- **Automation**: Fixed the `pin-core` recipe in the `justfile` to correctly align the core pin in `action.yml`.

## [2.5.1] - 2026-07-03

### 🔒 Security Advisory

- **Core Update**: Bumped Zenzic core dependency to `>=0.19.3` to mitigate the `Z205` (Forbidden Scheme) security gate bypass vulnerability (Double Href & Encoding Evasion).

### Changed

- **Dependencies**: Pinned Zenzic core to `0.19.3` to restore the deterministic execution environment.

## [2.5.0] - 2026-07-01

## [2.4.0] - 2026-06-28

### Changed

- **Core Update**: Pinned Zenzic core dependency to version `0.18.0` for full "Nuclear Static" compliance.
- **Automation**: Fully automated the release pipeline, synchronizing `bump-my-version` across `SECURITY.md`, `RELEASE.md`, `CHANGELOG.md`, and `CONTRIBUTING.md` to eliminate manual drift.

## [2.3.1] - 2026-06-27

### Added

- **SourceRank Visibility**: Added `requirements.txt` to expose Zenzic core dependency to ecosystem crawlers.
- **Ecosystem Gate**: Upgraded `just versions` to perform parity validation between `action.yml` and `requirements.txt`.

### Changed

- **Perimeter Hygiene**: Added `requirements.txt` to `excluded_file_patterns` in `.zenzic.toml` to prevent `Z405` violations.
- **Automation**: Updated `just pin-core` to propagate Zenzic core pins to `requirements.txt`.

## [2.3.0] - 2026-06-27

### Changed

- **Governance**: Modernized pull request template for English-only python ecosystem.

## [2.2.2] - 2026-06-23

### Changed

- **Dependencies**: Pinned Zenzic core to `0.15.1`.

## [2.2.1] - 2026-06-21

### Fixed

- **SARIF**: Filtered out info-level notes from SARIF findings count.

## [2.2.0] - 2026-06-21

### Changed

- **Engine Upgrade**: Upgraded Zenzic Core to `v0.15.0`.

## [2.1.1] - 2026-06-21

### Fixed

- **Core Update**: Compatibility adjustments and version bumps.

## [2.1.0] - 2026-06-21

### Changed (Breaking)

- **Dropped Docusaurus Support**: Upgraded the pinned Zenzic Core to `v0.13.0`, which surgically eradicates the Docusaurus adapter due to ontological incompatibility (React-injected IDs and MDX partial merging). Projects still relying on Docusaurus MUST remain on the `v1` floating tag (`v1.3.x`).
- **Major Version Bump**: The action major version is bumped to `v2` to prevent breaking existing Docusaurus consumers tracking `v1`.

### Fixed

- **Config Templates**: Enforced "Root-First, Table-Last" structure in `.zenzic.toml` and `.zenzic.local.toml` templates to prevent TOML root keys from being silently swallowed by preceding table declarations.

---

## Historical Releases

- v1.x archive: [changelogs/v1.x.md](./changelogs/v1.x.md)
- Archive index: [changelogs/README.md](./changelogs/README.md)
