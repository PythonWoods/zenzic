<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.13.0] - 2026-06-19

### Added

- **Active Defense:** Implemented strict TOML schema validation to instantly detect and reject root keys silently swallowed by nested `[tables]` in `.zenzic.toml` and `pyproject.toml`.
- **D.I.A. Compliance:** Added the "TOML Root Key Law" documentation enforcing explicit ordering for configuration boundaries.

### Changed

- **Refined CLI UX:** `inspect codes` now displays Severity and explicit `FATAL`/`HALT` pipeline blockers instead of misleading `0.0` penalties for security and governance-gate codes. `check` command now explicitly prints the final DQS score and gate status (`DQS Final Score: X/100 (Gate Passed/Failed)`) in the report footer.
- **Engine-Neutral Configuration Templates:** Removed Docusaurus from initialized `.zenzic.toml` templates and CLI help descriptions, defaulting to `mkdocs` and `zensical`.
- **Simplification of VSM Routing:** Eradicated Docusaurus-specific slug map initialization and routing rules during Virtual Site Map (VSM) construction.
- **Improved Resolver Robustness:** Standardized site root resolution and monorepo path checks inside `InMemoryPathResolver`.
- **Full documentation migration to Zensical/MkDocs.**

### Fixed

- **REUSE compliance updates and Z-Code parity fixes across the bilingual documentation.**

---

## Historical Releases

- v0.12.x archive: [changelogs/v0.12.md](./changelogs/v0.12.md)
- v0.11.x archive: [changelogs/v0.11.md](./changelogs/v0.11.md)
- v0.10.x archive: [changelogs/v0.10.md](./changelogs/v0.10.md)
- v0.9.x archive: [changelogs/v0.9.md](./changelogs/v0.9.md)
- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
