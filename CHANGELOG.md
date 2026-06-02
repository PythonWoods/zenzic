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

### Fixed

- Core scanner integration fix for `Z403 MISSING_ALT_TEXT` to align fixture coverage with production scan paths.
- Fixture line-number correction in scanner test cases to keep finding locations deterministic and stable.

---

## [0.9.0] - 2026-05-31

### Added

- `zenzic score --stamp`: deterministic, in-file badge stamping for score telemetry.
- `zenzic score --check-stamp`: config-aware freshness gate for stamped score badges.
- `badge_stamp_files` project metadata key to declare stamp targets.
- Domain-aware discovery exemptions for source-code assets in unused-asset analysis.
- `zenzic lab` command: empirical sandbox gallery covering 100% of Z-codes (20 scenarios).
- 15 new sandbox directories under `examples/` (z102 through z505), each with `.zenzic.toml`, `README.md`, and a minimal `docs/` tree that reliably triggers the target rule.
- `zenzic lab all` validation gate: all 20 scenarios emit the expected exit code.

### Changed

- Suppression debt model migrated to flat-cost scoring (one point per suppression).
- `suppression_cap` behavior clarified as an independent hard-fail governance gate.
- Local overlay parsing hardened with strict unknown-key rejection.
- `just verify` standardized to a five-step operational sequence (hooks, tests, strict check, stamp, freshness check).
- **Performance — Z204 (FORBIDDEN_TERM):** `scan_line_for_forbidden_terms` now accepts a pre-compiled RE2 union regex. `ZenzicConfig` builds the union once via `_recompile_forbidden_patterns()` (called in `model_post_init` and after every `_apply_local_toml` merge). Scan complexity reduced from O(N_lines × N_patterns) to O(N_lines).
- **Performance — Z601 (BRAND_OBSOLESCENCE):** `BrandObsolescenceRule` replaced per-pattern `list[RegexPattern]` with a single RE2 union pattern compiled once at `__init__`. Same O(N_lines) reduction.

### Removed

- Legacy adapter methods `map_url()` and `classify_route()` from the public adapter contract.
- Legacy score export path `--export-shields` in favor of native stamp/check-stamp telemetry.

---

## Historical Releases

- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
