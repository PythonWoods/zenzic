<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Fixed

- **LSP Diagnostics**: Hooked `check_snippet_content` into the `LanguageServer` loop. The editor now reports structural errors (like `Z503 SNIPPET_ERROR`) in real-time, bridging the feature gap between `zenzic check` and the LSP.

## [0.21.0] - 2026-07-11

## [0.21.0] — 2026-07-11

### ✨ Shift-Left to the Keystroke

This minor release introduces the foundational architecture for the Zenzic Language Server, pushing host-side feedback loops directly into editor environments.

### Added

- **Zenzic Language Server (ZLS) Foundation:** Introduced the `zenzic lsp` command, establishing a zero-dependency JSON-RPC 2.0 transport layer over `stdio`.
- **Zero-DBT Incremental Synchronization:** Implemented a UTF-16 compliant Incremental Document Manager (`textDocumentSync = 2`), solving impedance mismatches with Python string lengths and Unicode surrogate pairs.
- **Architectural Purple Teaming & Robustness:** Implemented PEP 484 `TypedDict` assertions across the IPC boundary to block schema desynchronizations, and hardened the `didClose` handlers for strict AST memory hygiene.
- **Debounced Diagnostic Emission:** Connected the $O(N)$ Z-Code validation pipeline to `publishDiagnostics`. Integrated I/O multiplexing (`select.select`) directly within the standard synchronous loop to securely enforce a 300ms CPU protection debounce without requiring `asyncio`.

## Historical Releases

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
