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

## [v0.15.0] - The Semantic Hygiene Update (Next)

*Immediate focus. Zero blocking architectural dependencies.*

- **Z603 DEAD_SUPPRESSION:** Detects inline `zenzic:ignore` directives that do not correspond to any active finding. Eliminates phantom technical debt.
- **Z108 STALE_ALLOWLIST_ENTRY** (Issue #70): Config-hygiene check for unused `absolute_path_allowlist` entries in `.zenzic.toml`. Implements config-parsing logic to cross-reference allowlist entries against the resolved file tree.
- **Semantic Schemas Validation:** YAML/JSON frontmatter validation against strictly declared schemas (e.g., `required_fields: [title, description]`).

## [v0.16.0] - The AST Foundations

*Laying the groundwork for automation and third-party rules.*

- **Deterministic Markdown Renderer** (Issue #11): A stable AST-to-Markdown rendering engine. Requirement for a loss-less AST-to-string serializer that perfectly preserves original whitespace, lists, and HTML artifacts.
- **Custom Rules API v2 (AST Walker):** Stable AST adapter and rule APIs with a semver guarantee. The `BaseASTRule` signature must pass `MdASTNode` objects and enforce a strict RE2 execution boundary with a 50ms timeout (`Z902`).
- **Z407 BROKEN_CODE_REFERENCE:** Scan Markdown for backtick-quoted paths and verify their physical existence. *(Depends on Custom Rules API to support explicit Markdown attribute opt-in like `{: .verify-path }` before implementation).*

## [v0.17.0] - The Automation Era

*Leveraging v0.16.0 foundations to shift documentation quality left.*

- **Deterministic Auto-Fix Engine (`zenzic fix`)** (Issue #10): Semantic `--dry-run` / `--apply` repair semantics for `Z1xx` and `Z3xx` findings. Powered by the Deterministic Markdown Renderer. Implements an exact 3-Tier safety model (Tier 1: Auto-apply, Tier 2: Patches, Tier 3: Security FATALs banned).
- **Zenzic LSP (Language Server Protocol)** (Issue #12): A lightweight LSP implementation providing real-time IDE diagnostics and code-actions. Hooks into the Auto-Fix engine to provide native IDE "Quick Fix" actions.
- **Semantic Linting & Readability** (Issues #8, #9): AST-based rules to detect semantically duplicate headings, empty/stub sections, and integration of deterministic readability metrics (Flesch-Kincaid).

## [v0.18.0] - Ecosystem & Interoperability

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

Roadmap last updated: 2026-06-22
