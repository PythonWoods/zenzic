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

## [0.10.2] - 2026-06-07

### Fixed

- **Core Engine (AST Parser):** Fixed a blindspot in the AST parser where image nodes (`![alt][id]`) were not being harvested into the `used_ids` set, causing false-positive Z302 (Orphan Definition) warnings.
- **Core Engine (Path Resolver):** The local path resolver now strips URL fragments (`#...`) and query strings (`?...`) before interrogating the filesystem. This prevents false-positive Z101/Z104 errors when using GFM suffixes on local file links (e.g., `../assets/img.png#gh-light-mode-only`).

---

## [0.10.1] - 2026-06-07

### Changed

- Refactored `--ci` to act as a global macro-flag, implicitly suppressing ASCII headers across all commands.

---

## [0.10.0] - 2026-06-06

### Added

- **Native GitHub Annotations:** Added `--format github-annotations` which outputs findings using the `::error::` workflow command syntax, allowing GitHub Actions to natively inject inline review comments directly into PR diffs.
- **CI Shorthand:** Added `--ci` flag, which automatically sets `--strict` mode (warnings become errors) and enables `--format github-annotations`, standardizing the CI integration.
- **Targeted Filtering:** Added `--only` flag (e.g. `--only Z104,Z201`) to perform destructive filtering of findings at the engine level. This enables progressive adoption of Zenzic on legacy repositories by letting teams start with critical rules before expanding scope.
- **Added:** Asynchronous network engine based on `asyncio` and `httpx` for concurrent external link validation (Z109).
- **Added:** Atomic local caching (`.zenzic_cache/external_links.json`) with configurable 24h TTL to eliminate latency in repeated executions.
- **Added:** Smart Fallback (HEAD -> GET stream) to bypass servers blocking HEAD requests (e.g., 403/405).
- **Added:** New TOML configuration `[network]` for granular cache control.

---

## Historical Releases

- v0.9.x archive: [changelogs/v0.9.md](./changelogs/v0.9.md)
- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
