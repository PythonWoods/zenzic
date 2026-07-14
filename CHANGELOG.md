<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [0.22.3] - 2026-07-14

### Changed

- **Architectural Unification:** Removed the legacy ad-hoc `placeholders` tracking system from CLI reports and JSON schemas. Z501 (Placeholders) and Z502 (Short Content) rules are now fully integrated into the standard `AdaptiveRuleEngine` lifecycle, ensuring parity between CLI and LSP behaviors.

### Fixed

- **ZLS Diagnostic Parity:** Resolved an architectural drift where the Language Server failed to emit specific structural and hygiene diagnostics compared to the CLI.
  - **Zero-Config Parity:** `Z501` (Placeholder) and `Z502` (Short Content) now correctly bootstrap with default parameters in Standalone Mode (no `.zenzic.toml`).
  - **Dead Suppression (`Z603`):** The ZLS now correctly collects and emits dead suppression warnings at the end of the real-time diagnostic pipeline.
- **URP Execution Order:** Fixed an issue where the Virtual Site Map (VSM) resolution (`Z101`) masked critical security and structural rules (`Z202`, `Z203`, `Z105`). The Uniform Resolver Pipeline now strictly evaluates path traversal and absolute path prohibition *before* checking file existence.
- **Polyglot Extractor (`Z121`):** Reordered attribute validation to ensure `Z121` (Missing Href) is not masked by `Z120` (Unknown Attribute) on malformed HTML tags.

## [0.22.2] - 2026-07-14

### Fixed

- **ZLS Architecture:** Completely decoupled the Uniform Resolver Pipeline (URP) to support in-memory document validation. The Language Server now guarantees 100% diagnostic parity with the CLI for structural link checks (Z102, Z104, Z105) without redundant disk I/O.
- **Rule Unification:** Refactored `Z403` (Missing Alt Text) into a native `BaseRule` to eliminate legacy hardcoded execution paths.

## [0.22.1] - 2026-07-14

### Fixed

- **Language Server (LSP):** Resolved a silent failure in the diagnostic pipeline where `textDocument/didOpen` and `textDocument/didChange` events failed to trigger the rule engine. The server now correctly dispatches diagnostics back to the VS Code client via the debounce multiplexer.

## [0.22.0] - 2026-07-12

### ✨ Real-Time Global Topological Awareness (VSM)

This release introduces Real-Time Virtual Site Map (VSM) integration into the Zenzic Language Server (ZLS), ensuring structural checks are validated instantaneously across the entire workspace.

### Added

- **Synchronous VSM Initialization:** The Language Server now seamlessly intercepts the `workspace/workspaceFolders` payload during the `initialize` handshake to perform a synchronous, zero-threading build of the global VSM.
- **O(1) Incremental Patching:** Implemented `workspace/didChangeWatchedFiles` capability to dynamically watch the repository. File creations, deletions, and updates trigger an $O(1)$ dictionary patch, avoiding full re-evaluations and preventing race conditions.
- **Real-Time Structural Validation:** Z-Codes such as `Z101 Broken Link`, `Z104 File Not Found`, and `Z105 Absolute Path` are now resolved and reported dynamically in real-time as files are created or deleted across the workspace.

## Historical Releases

- v0.21.x archive: [changelogs/v0.21.x.md](./changelogs/v0.21.x.md)
- v0.20.x archive: [changelogs/v0.20.x.md](./changelogs/v0.20.x.md)
- v0.19.x archive: [changelogs/v0.19.x.md](./changelogs/v0.19.x.md)
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
