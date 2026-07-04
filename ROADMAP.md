<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# Zenzic Roadmap

> **Governance Note (ADR-020):** This document is a root governance file. It is strictly **English-Only**. It must not be translated or mirrored in the `i18n/` directory.

This document describes the planned milestone trajectory for Zenzic.
Dates are targets, not commitments. All milestones are subject to revision.

For the current release history, see [CHANGELOG.md](CHANGELOG.md).

---

## Recent Releases

### [v0.18.0] - Zenzic Routing Kernel (Completed)

- **Zenzic Deterministic Routing Kernel**: Disjoint Domain Model utilizing explicit static mapping for loop-free, 100% deterministic edge resolution (Nuclear Static v12).

---

### [v0.19.0] - The AST Foundations (Completed)

*Lossless AST Parser, O(N) Inline Tokenization, Mutator Engine, Atomic File Writer, Z108 Auto-Fix.*

---

### [v0.20.0] - The Extensibility Update (Completed)

*Custom Rules API v2, deterministic visitation sandbox, auto-fix expansion.*

- **Custom Rules API v2 (AST Walker):** Users subclass `BaseASTRule` from `zenzic.rules`. Rules are auto-discovered from `.zenzic/rules/*.py` — no registration required.
- **Deterministic Visitation Budget Sandbox (Z901 / Z902):** Single-threaded visitation counter guard (`max_visits = 10 000`) replaces thread-based or signal-based timeouts, preserving Windows compatibility and the $O(N)$ invariant.
- **Auto-Fix Expansion:** `zenzic fix` now auto-repairs **Z121** (MISSING_OR_EMPTY_HREF → `href="#"`) and **Z603** (DEAD_SUPPRESSION comment/attribute removal).
- **`fixable` metadata field:** `CodeDefinition` exposes `fixable: bool`, surfaced in `zenzic explain` and `finding-codes.md`.

---

### [v0.20.1] - UI & Polyglot Leak Patch (Completed)

- **UI dark mode restoration:** Reverted LCP optimization purging to stabilize the slate-based dark theme.
- **Polyglot URP bypass & Z603 Dead Suppression paradox resolution:** Native HTML suppression (`data-zenzic-ignore`) correctly short-circuits the resolver pipeline (URP) and marks directives as consumed to prevent dead suppression warnings (Z603).

---

## [v0.21.0] - Shift-Left to the Keystroke (IDE Integration & LSP)

*Pushing the "Hostile Precision" feedback loop directly into the authoring environment.*

- **Zenzic Language Server (ZLS) & VS Code Extension:** To push the "Hostile Precision" feedback loop from the CI/CD pipeline directly into the authoring environment, Zenzic will implement a native Language Server Protocol (LSP) interface.
  - **The Architecture:** The core engine will expose a `zenzic.lsp` module (JSON-RPC over stdio). An official, thin VS Code Extension (written in TypeScript) will act purely as an LSP client.
  - **The Single Source of Truth:** The VS Code extension will contain zero AST parsing or regex logic. It will stream `textDocument/didChange` events to the local Python backend. The Python core remains the sole arbiter of Document Quality.
  - **Real-Time Governance:** Z-Codes will render as real-time editor diagnostics (red/yellow squiggly lines). Hovering over a broken link (`Z104`), a missing anchor (`Z102`), or a leaked credential (`Z201`) will display the exact DQS penalty and remediation steps natively extracted from the Python `CodeDefinition` registry.
  - **Performance Invariant:** Leveraging the $O(N)$ RE2 DFA engine and atomic caching, the ZLS will guarantee sub-50ms diagnostic responses, ensuring zero typing latency degradation for the end-user.
- **Semantic Linting & Readability** (Issues #8, #9): AST-based rules to detect semantically duplicate headings, empty/stub sections, and integration of deterministic readability metrics (Flesch-Kincaid).

## [v0.22.0] - Ecosystem & Interoperability

*Expanding the Zenzic perimeter to external frameworks.*

- **The Bridge Architecture (TypeScript Docusaurus Plugin):** An official NPM plugin (`@zenzic/plugin-docusaurus`) that dumps a `.zenzic-vsm.json` artifact during the build.
- **Community: Sphinx Adapter** (Issue #51): Support for parsing Sphinx `.rst` and `.md` documentation trees.
- **Community: Hugo Adapter** (Issue #50): Support for Hugo's specific `hugo.toml` configuration and frontmatter conventions.
- **Smart Link Graph** (Issue #7): Build a directed graph of the documentation to detect unlinked pages (islands) and navigation cycles.

---

## Invariants (all milestones)

These constraints apply across every future release:

| Invariant | Description |
|-----------|-------------|
| Zero Subprocess | `subprocess.Popen` and `os.system` permanently banned from `src/`. |
| Pure Functions | The analysis engine has zero global state. |
| DFA Guarantee | All regex matching backed by RE2. O(n) complexity. |
| Exit Code Contract | Exit 2 = credential; Exit 3 = traversal. Never renumbered. |
| No Inference | Zero inference-engine runtime dependencies declared in `pyproject.toml`. |

---

## Known Bugs & Deferred Work

No known bugs.

---

Roadmap last updated: 2026-07-04
