<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Zenzic Language Server (ZLS) Integration

> **ADR coverage:** ADR-075 (Radical Unawareness), ADR-020 (Mirror Law), ADR-013 (RE2 Discipline)

## JSON-RPC `stdio` Interface

The `LanguageServer` class in `zenzic.lsp.server` acts as a **stateless transport proxy**: it reads JSON-RPC 2.0 messages from `stdin` and writes responses and notifications to `stdout`. It holds no knowledge of file relationships, graph topology, or cross-document dependencies.

Supported lifecycle events:
| Method | Action |
|---|---|
| `initialize` | Load `ZenzicConfig`, build `AdaptiveRuleEngine`, set `repo_root` |
| `initialized` | Trigger `_build_vsm_sync()`, register `workspace/didChangeWatchedFiles` |
| `textDocument/didOpen` | Inject buffer into `VirtualBufferOverlay`, mark URI dirty |
| `textDocument/didChange` | Update overlay buffer, mark URI dirty (debounced 300ms) |
| `textDocument/didClose` | Evict buffer from overlay |
| `textDocument/hover` | Query VSM route for typed `ZenzicDiagnostic`, serialize at boundary |
| `workspace/didChangeWatchedFiles` | Patch VSM route table O(1) per change |

## Strict Diagnostic Typing

All diagnostics are represented internally as `ZenzicDiagnostic` dataclass instances (defined in `zenzic.models.diagnostics`):

```python
@dataclass(frozen=True)
class ZenzicDiagnostic:
    range: DiagnosticRange      # DiagnosticPosition(line, character) × 2
    severity: Severity          # IntEnum: ERROR=1, WARNING=2, INFORMATION=3
    code: str                   # Z-Code string, e.g. "Z101"
    source: str                 # Always "zenzic"
    message: str                # Human-readable description
```

The `to_lsp_dict()` method is the **single serialization boundary**. Untyped dicts are never used for diagnostic payloads; `Any` is forbidden in the diagnostic model.

## VirtualBufferOverlay

`VirtualBufferOverlay` (in `zenzic.models.vsm`) serves two purposes:

1. **Buffer registry**: maps `file://` URIs to live in-memory text, replacing disk reads during validation.
2. **Reverse index owner**: maintains `incoming_links: dict[str, set[Path]]`, a mapping from canonical URL to the set of files that link to it. This is the sole location tracking graph topology.

The `update()` method automatically calls `_reindex_outgoing_links()`, which re-parses the changed buffer's Markdown links and HTML nodes via `_extract_inline_links_with_lines` and `PolyglotExtractor`, rebuilding the relevant reverse-index entries in O(link count) time.

```text
overlay.dependents_of(canonical_url) -> frozenset[Path]   # O(1)
overlay.update(uri, content)                               # O(links in buffer)
overlay.remove(uri)                                        # O(total URLs in index)
```

## Incremental VSM Update Mechanism

Upon a `didChange` event:

1. **Incremental buffer update** — only the modified URI is re-read from `overlay.buffers`; `md_contents_cache` and `anchors_cache` are patched in-place.
2. **VSM patch** — `build_vsm` is called on the full `md_contents_cache` (already in memory); no disk reads occur.
3. **Dependent expansion** — for each modified file, the server calls `overlay.dependents_of(canonical_url)` to retrieve the set of files that contain links resolving to the modified file. This is O(1).
4. **Targeted validation** — the `AdaptiveRuleEngine` and `_run_incremental_urp` run only against the modified file and its dependents.
5. **Typed store** — `route.diagnostics: list[ZenzicDiagnostic]` is replaced atomically.
6. **Serialization boundary** — `[d.to_lsp_dict() for d in route.diagnostics]` produces the `publishDiagnostics` payload. This is the only location where typed diagnostics are converted to dicts.
