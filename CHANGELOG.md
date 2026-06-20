<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.14.0] - Unreleased

### Breaking Changes

- **Z602 I18N_PARITY Engine Removed (ADR-034):** The bilingual parity scanner (`find_i18n_parity`) has been completely removed from the Zenzic engine. Z602 remains in the code namespace as **INACTIVE** for configuration forward-compatibility, but the scanner emits **zero findings**. Projects using `[i18n]` configuration will no longer trigger Z602 — the section is silently ignored by the config loader. The `I18nConfig` and `I18nSource` models have been removed from `zenzic.models.config`.
- **`LEGACY_TO_CODE` removed from `zenzic.core.codes`:** The migration alias dictionary mapping legacy `Z9xx` codes (`Z903`, `Z904`, `Z905`, `Z907`) to their canonical successors has been deleted. Direct consumers of this symbol must update to the canonical codes directly.
- **`ZenzicConfig.i18n` field removed:** The `i18n: I18nConfig` field no longer exists on `ZenzicConfig`. Runtime access will raise `AttributeError`.
- **`CodeDefinition` gains a `status` field:** The `NamedTuple` now has a fourth field `status: str = "active"`. This is backward-compatible for structural pattern matching but may affect code doing positional tuple construction.

### Removed

- `find_i18n_parity()` function from `zenzic.core.scanner` — 443 lines of scanner logic deleted.
- `I18nParityIssue` dataclass from `zenzic.core.scanner`.
- `I18nConfig` and `I18nSource` models from `zenzic.models.config`.
- `ZenzicConfig.i18n` field.
- `LEGACY_TO_CODE` dict from `zenzic.core.codes`.
- Z602 entry from `FROZEN_CODES` (code remains in registry as `status="inactive"`).
- Z602 `CoreScanner` descriptor from `CORE_SCANNERS`.
- `tests/test_i18n_parity.py` — 100+ contract tests for the now-removed scanner.
- `# i18n_parity = false` commented field from all `zenzic init` templates.

### Added

- **Z506 MALFORMED_FRONTMATTER (built-in always-active):** New rule that detects malformed YAML frontmatter delimiters on line 1 of a Markdown file. Any opening line that starts with `--` but is not exactly `---` (e.g. `--`, `----`, `--- trailing chars`) causes the entire frontmatter block to be silently discarded by most static-site engines, rendering `title:` and all metadata keys as raw prose. Severity `error`, −5.0 pts (Content), suppressible via `<!-- zenzic:ignore: Z506 -->`.

### Fixed

- **JSON Formatter Bypass:** Fixed a critical bug in `check` where the JSON output bypassed governance filtering. Zenzic now correctly applies `per_file_ignores` and `directory_policies` to the JSON output.
- **Z405 Infrastructure Exclusions:** Natively exempted standard infrastructure files (`robots.txt`, `_redirects`, `CNAME`, `sitemap.xml`) from the Z405 Unused Assets check.
- **Obsolete Code References:** All internal comments referencing legacy `Z903`/`Z905` codes updated to the canonical `Z405`/`Z601` codes.

---

## [0.13.1] - 2026-06-19

### Fixed

- **SARIF Formatter Bypass:** Fixed a critical bug in `check` where the SARIF JSON output bypassed `per_file_ignores` and `directory_policies` filtering. Zenzic now correctly applies governance exclusions to the SARIF output, ensuring only active (unsuppressed) findings are exported to GitHub Advanced Security.

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
