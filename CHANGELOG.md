<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [0.19.3] - Unreleased

### Fixed

- **Security:** Resolved a Z205 bypass vulnerability where maliciously encoded HTML entities or duplicated href attributes could evade the forbidden scheme detection.

## [0.19.2] — 2026-07-02

### Fixed

- **Performance (LCP):** Optimized Critical Rendering Path by injecting `<link rel="preconnect">` resource hints for the GitHub API, significantly reducing latency for client-side widgets.
- **Performance (CSS):** Implemented strict Tailwind CSS purging via `tailwind.config.js`, removing unused utility classes and minimizing the frontend payload.

### Technical Details

- **DQS Invariant:** Repository Documentation Quality Score remains verified at 100/100.

## [0.19.1] - 2026-07-02

### Fixed

- **Accessibility:** Resolved WCAG 2.1 AA contrast failures across homepage templates by shifting light mode secondary text to `zinc-600` and dark mode secondary text to `zinc-400`.
- **Accessibility:** Added accessible name via `aria-label="Search dialog"` to the search dialog component for screen readers and agentic navigation.
- **Performance:** Self-hosted Google Font files (Inter, IBM Plex Mono, Barlow Condensed, JetBrains Mono) for offline compliance and LCP optimization.

## [0.19.0] - 2026-07-01

### Added

- Lossless AST parser and serializer (Composite Pattern) for Markdown blocks and inline elements.
- O(N) character-by-character state machine for inline tokenization, eliminating regex backtracking.
- Mutator engine for non-destructive in-memory AST modifications.
- Atomic File Writer implementing a strict write barrier with `tempfile` and `os.replace`.
- `zenzic fix` CLI command with `--dry-run` and `--apply` modes.
- `Z108 (EMPTY_LINK_TEXT)` auto-fix support, injecting the `TODO` keyword to transition structural errors into content debt.

### Fixed

- **Z501 (Placeholder Content):** Fixed context-blindness that caused placeholders inside fenced code blocks to trigger false positives. Restored default placeholder patterns in standard configurations.

## Historical Releases

- v0.18.x archive: [changelogs/v0.18.x.md](./changelogs/v0.18.x.md)
- v0.17.x archive: [changelogs/v0.17.x.md](./changelogs/v0.17.x.md)
- v0.16.x archive: [changelogs/v0.16.x.md](./changelogs/v0.16.x.md)
- v0.15.x archive: [changelogs/v0.15.x.md](./changelogs/v0.15.x.md)
- v0.14.x archive: [changelogs/v0.14.md](./changelogs/v0.14.md)
- v0.13.x archive: [changelogs/v0.13.md](./changelogs/v0.13.md)
- v0.12.x archive: [changelogs/v0.12.md](./changelogs/v0.12.md)
- v0.11.x archive: [changelogs/v0.11.md](./changelogs/v0.11.md)
- v0.10.x archive: [changelogs/v0.10.md](./changelogs/v0.10.md)
- v0.9.x archive: [changelogs/v0.9.md](./changelogs/v0.9.md)
- v0.8.x archive: [changelogs/v0.8.md](./changelogs/v0.8.md)
- v0.1.x–v0.7.x archive index: [changelogs/README.md](./changelogs/README.md)
