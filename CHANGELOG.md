<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [0.23.1] - 2026-07-22

### Added

- **LSP Diagnostic Payload Formatting (`ZenzicDiagnostic.to_lsp_dict()`)**: Added `codeDescription` property with `href` pointing to `https://zenzic.dev/docs/reference/finding-codes#{code}` and prepended `[{code}] ` prefix to diagnostic messages per LSP 3.16/3.17 specifications (`ZLS-UX-001-DIAGNOSTIC-FORMATTING`).

## [0.23.0] - 2026-07-18

### Added

- **`IncrementalAnalysisEngine`** (`zenzic.core.incremental`): Standalone, transport-agnostic engine for O(K) incremental documentation analysis. Exposes a deterministic `process_changes(vsm, overlay, changed_uris)` API returning `dict[str, list[ZenzicDiagnostic]]`. Zero knowledge of JSON-RPC, LSP, or VS Code (ADR-075).
- **Engine isolation test suite** (`tests/test_incremental_engine.py`): 8 tests covering full sync, incremental analysis, cross-file anchor invalidation, determinism, import graph compliance, latency benchmark (<50ms), virtual route enforcement, and deleted file route removal.
- **`ZenzicDiagnostic` dataclass** (`zenzic.models.diagnostics`): Strict, frozen dataclass representing a diagnostic payload. Eliminates all `Any` and untyped `dict` usage from the diagnostic model. LSP serialization occurs exclusively via `ZenzicDiagnostic.to_lsp_dict()`.
- **`VirtualBufferOverlay.incoming_links`**: Reverse index (`canonical URL → set[Path]`) relocated from the LSP server into the VSM layer. Provides O(1) dependent-file lookups via `overlay.dependents_of()` while upholding ADR-075 (Radical Unawareness).
- **ZLS Incremental Validation**: `_sync_workspace_and_publish` performs targeted, graph-aware validation. Only the changed file and its reverse-index dependents are re-evaluated; unmodified files are never re-parsed.
- **Architectural Documentation**: `docs/architecture/lsp-integration.md` — detailed description of the JSON-RPC lifecycle, `VirtualBufferOverlay`, reverse index, and serialization boundary.

### Changed

- **`LanguageServer`** refactored to delegate all analysis to `IncrementalAnalysisEngine`. The server now handles only JSON-RPC serialization/deserialization and stream management (926 → 470 lines, −49.2%).
- **`_sync_workspace_and_publish`** reduced from ~280 lines of inline analysis to ~25 lines of engine delegation + transport serialization.
- **Cache ownership**: `md_contents_cache` and `anchors_cache` moved from `LanguageServer` to `IncrementalAnalysisEngine`. Server delegates via `engine.update_file_cache()` / `engine.remove_file_cache()`.
- **`Route.diagnostics`** now typed as `list[ZenzicDiagnostic]` (previously `list[dict[str, Any]]`). Enforces strict typing at the VSM layer.
- **`LanguageServer`** stripped of all topology state (`incoming_links`, `file_diagnostics`). The server is now a pure transport proxy as required by ADR-075.

### Removed

- **`LanguageServer._run_incremental_urp()`** (208 lines): URP checks moved to `IncrementalAnalysisEngine._run_urp_checks()`.
- **`LanguageServer._to_utf16_col()`** (9 lines): Moved to `zenzic.core.incremental._to_utf16_col()`.
- **Graph topology state from LSP layer**: `incoming_links` and `file_diagnostics` removed from `LanguageServer`. All dependency tracking is now owned by `VirtualBufferOverlay`.

## Historical Releases

- v0.22.x archive: [changelogs/v0.22.x.md](./changelogs/v0.22.x.md)
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
