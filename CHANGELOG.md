<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

- `zenzic score --stamp`: deterministic, in-file badge stamping for score telemetry.
- `zenzic score --check-stamp`: config-aware freshness gate for stamped score badges.
- `badge_stamp_files` project metadata key to declare stamp targets.
- Domain-aware discovery exemptions for source-code assets in unused-asset analysis.

### Changed

- Suppression debt model migrated to flat-cost scoring (one point per suppression).
- `suppression_cap` behavior clarified as an independent hard-fail governance gate.
- Local overlay parsing hardened with strict unknown-key rejection.
- `just verify` standardized to a five-step operational sequence (hooks, tests, strict check, stamp, freshness check).

### Removed

- Legacy adapter methods `map_url()` and `classify_route()` from the public adapter contract.
- Legacy score export path `--export-shields` in favor of native stamp/check-stamp telemetry.

---

## Historical Releases

- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
