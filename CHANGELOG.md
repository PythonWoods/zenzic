<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.18.0] - 2026-06-28

### Added

- **Zenzic Routing Kernel**: Transitioned from static `_redirects` configuration to a verifiable edge router compiler.
  - Auto-generates a deterministic `O(depth)` Cloudflare Worker (`worker.js`).
  - Auto-generates a pre-deploy test matrix (`test.js`) to certify zero-ambiguity across topological routes.
  - Enforces ADR-001 ("Lint the Source, Not the Build"), solidifying `docs/_redirects` as the Single Source of Truth (SSOT).
  - Implements a Safe Hub Sink (`/docs/* -> /`) to structurally prevent `splat` hallucinations.

## [0.17.0] - 2026-06-28

### Added

- **Polyglot Extractor (Uniform Resolver Pipeline)**: Deep HTML parsing for `<a>` and `<img>` tags inside Markdown documents to eliminate the "HTML Shadow Zone", via a DFA-native Google RE2 engine.
- **Diagnostic codes Z120-Z124 (HTML Integrity)**:
  - `Z120 UNKNOWN_HTML_ATTRIBUTE`: Warns about non-standard attributes outside the Safe-Core list.
  - `Z121 MISSING_OR_EMPTY_HREF`: Flags missing or empty `href`/`src` attributes.
  - `Z122 JUMP_LINK_DETECTED`: Warns on opaque JavaScript anchors (`href="#"`).
  - `Z123 NON_HTTP_SCHEME`: Informational code for schemes like `mailto:` or `tel:`.
  - `Z124 OPAQUE_HTML_CONTEXT`: Flags event handlers or shadow-routing attributes.
- **Z205 Forbidden Scheme (Security Gate)**: Hard-coded, non-suppressible protection against cross-site scripting (XSS) vectors (e.g., `javascript:` or `data:` schemas). Halts the pipeline with Exit 2 and outputs `executionSuccessful: false` in SARIF `toolExecutionNotifications`.
- **Z118 Stale Global Suppression**: Enforces zero-debt configurations by flagging `directory_policies` in `.zenzic.toml` that attempt to suppress rules never violated during the scan.
- **SARIF Security Mapping**: `toolExecutionNotifications` in SARIF outputs now properly reflect critical execution interruptions like `Z201` and `Z205`.

### Fixed

- **Z603 Redundancy Detection**: Fixed "blindness" to inline tags (`data-zenzic-ignore`) when a global `directory_policies` rule already covers the file.
- **MkDocs Strict Mode Orchestration**: Excluded orphaned assets and decoupled documentation artifacts from `mkdocs.yml` validation.
- **RSS/Atom Feed Validation**: Resolved Markdown link validation errors by adopting raw HTML (`data-zenzic-ignore="Z104"`) for dynamically generated feeds.

---

## Historical Releases

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
