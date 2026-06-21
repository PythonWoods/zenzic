<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.15.0] - Unreleased

### Added

- **Z603 DEAD_SUPPRESSION (governance, always-active):** Detects inline `zenzic:ignore`
  directives that do not correspond to any active finding.  A suppression comment that
  silences nothing is **Phantom Debt** — it consumes part of the 30-point governance
  budget without justification.  Severity `warning`, −1.0 pt (Governance), suppressible
  (the suppression of a Z603 is itself tracked recursively).  Implemented via a new
  `SuppressionTracker` per-file registry (`src/zenzic/core/suppressions.py`) that marks
  each directive as `consumed` when an active finding is suppressed; any unconsumed
  directive at end-of-file is reported as Z603.
  - **Inviolability Law preserved:** Z201/Z202/Z203/Z204 remain non-suppressible;
    attempting to suppress them with `zenzic:ignore` creates a dead directive, which
    itself triggers Z603.
  - **Fence-aware (ADR-084):** Directives inside fenced code blocks or backtick inline
    code spans are excluded from the tracker.

---

---

## Historical Releases

- v0.14.x archive: [changelogs/v0.14.md](./changelogs/v0.14.md)
- v0.13.x archive: [changelogs/v0.13.md](./changelogs/v0.13.md)
- v0.12.x archive: [changelogs/v0.12.md](./changelogs/v0.12.md)
- v0.11.x archive: [changelogs/v0.11.md](./changelogs/v0.11.md)
- v0.10.x archive: [changelogs/v0.10.md](./changelogs/v0.10.md)
- v0.9.x archive: [changelogs/v0.9.md](./changelogs/v0.9.md)
- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
