<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

No changes yet.

---

## [0.9.1] - 2026-06-02

### Added

- Native engine, fixtures, lab, and test validation coverage for `Z107 CIRCULAR_ANCHOR` (self-referential anchor link) and `Z104 FILE_NOT_FOUND`.

### Changed

- **Unified Score Exclusions Pipeline:** Refactored `zenzic score` calculations (`_run_all_checks` in `_standalone.py`) to run the exact same `_collect_all_results` -> `_to_findings` pipeline as `check all`. Suppression exclusions (`per_file_ignores` and `directory_policies`) are now applied identically to ensure DQS aligns perfectly with linter findings.
- **Repository-Relative Path Resolution:** Refactored path mapping across the core engine scanner (`scanner.py`), CLI check commands (`_check.py`), findings reporter (`reporter.py`), and governance filter (`_governance.py`) to strictly resolve all finding relative paths against `repo_root` instead of `docs_root`, eliminating path inconsistencies.
- **Badge Stamping Path Resolution:** Fixed `score --stamp` and `score --check-stamp` path resolution so that configured `badge_stamp_files` paths are resolved relative to the target project's `repo_root` instead of the process's working directory.

### Fixed

- Core scanner integration fix for `Z403 MISSING_ALT_TEXT` to align fixture coverage with production scan paths.
- Fixture line-number correction in scanner test cases to keep finding locations deterministic and stable.

---

## Historical Releases

- v0.9.x archive: [changelogs/v0.9.md](./changelogs/v0.9.md)
- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
