<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [0.19.5] - 2026-07-04

### Fixed

- **Core (Validator):** Hardened the Polyglot Extractor by masking HTML and MD/MDX comments to ignore tags within comments, preventing false-positive diagnostics and aligning with Markdown link scanning.
- **Core (Validator):** Aligned code fence detection in the Polyglot Extractor with `SuppressionTracker` by ignoring closing fences with trailing characters (e.g. ```` ```extra ````), preventing premature code block closure.

## [0.19.4] - 2026-07-04

### Fixed

- **Core (Mutator):** Hardened the Atomic Write Barrier to correctly follow symlinks during auto-fix operations, preventing the accidental overwriting of the symlink file itself.
- **Core (Mutator):** Implemented a robust `try...finally` cleanup routine to guarantee the removal of transient `.zenzic-tmp-*` files even if the process receives a `KeyboardInterrupt` (SIGINT) during an atomic write.
- **Diagnostics (Z108):** Enhanced the Z108 (Empty Link Text) regex and AST mutator to correctly detect and patch "formatted empty links" (e.g., `[**](url)` or `` [` `](url) ``), eliminating an AST drift edge-case.

## [0.19.3] — 2026-07-02

### 🔒 Security Advisory

This patch release addresses a security vulnerability in the Polyglot Extractor introduced in `v0.19.0`. All users utilizing Zenzic as a CI security gate are strongly advised to update immediately.

### Fixed

- **Security (Z205 Bypass):** Resolved a parser differential vulnerability where attackers could evade the `Z205` (Forbidden Scheme) security gate. The extractor now correctly adheres to the HTML5 "first-wins" attribute parsing rule, preventing "Double Href" injection attacks.
- **Security (Encoding Evasion):** The engine now correctly unescapes HTML entities and strips obfuscating control characters before evaluating URI schemes, preventing bypasses using encoded `javascript:` or `data:` payloads.

### Technical Details

- **Performance:** The security hardening maintains the strict $O(N)$ (RE2/DFA-pure) execution time invariant.
- **DQS Invariant:** Repository Documentation Quality Score remains verified at 100/100.

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
