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

## [0.10.0] - 2026-06-06

### Added

- **Native GitHub Annotations:** Added `--format github-annotations` which outputs findings using the `::error::` workflow command syntax, allowing GitHub Actions to natively inject inline review comments directly into PR diffs.
- **CI Shorthand:** Added `--ci` flag, which automatically sets `--strict` mode (warnings become errors) and enables `--format github-annotations`, standardizing the CI integration.
- **Targeted Filtering:** Added `--only` flag (e.g. `--only Z104,Z201`) to perform destructive filtering of findings at the engine level. This enables progressive adoption of Zenzic on legacy repositories by letting teams start with critical rules before expanding scope.
- **Added:** Motore di rete asincrono basato su asyncio e httpx per la validazione concorrente dei link esterni (Z109).
- **Added:** Caching locale atomico (`.zenzic_cache/external_links.json`) con TTL configurabile a 24h per azzerare la latenza nelle esecuzioni ripetute.
- **Added:** Smart Fallback (HEAD -> GET stream) per aggirare i server che bloccano le richieste HEAD (es. 403/405).
- **Added:** Nuova configurazione TOML `[network]` per il controllo granulare della cache.

---

## Historical Releases

- v0.9.x archive: [changelogs/v0.9.md](./changelogs/v0.9.md)
- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
