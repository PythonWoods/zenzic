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

## Layer 1: Core Engine & Foundations

*Architectural prerequisites required to unlock advanced tooling and automation.*

- **Deterministic Markdown Renderer** (Issue #11): A stable AST-to-Markdown rendering engine. Requirement for a loss-less AST-to-string serializer that perfectly preserves original whitespace, lists, and HTML artifacts, ensuring automated fixes do not reformat unrelated text. Required to persist automated fixes while preserving the author's original formatting intent.
- **Custom Rules API v2 (AST Walker):** Stable AST adapter and rule APIs with a semver guarantee. Exposes the internal CommonMark walker to third-party authors, moving beyond line-by-line regex. The `BaseASTRule` signature must pass `MdASTNode` objects and enforce a strict RE2 execution boundary with a 50ms timeout (`Z902`) per file to prevent third-party ReDoS.
- **Semantic Schemas Validation:** YAML/JSON frontmatter validation against strictly declared schemas (e.g., `required_fields: [title, description]`).

## Layer 2: Developer Experience & Automation

*Features dependent on Layer 1 foundations to shift documentation quality left.*

- **Deterministic Auto-Fix Engine (`zenzic fix`)** (Issue #10): Semantic `--dry-run` / `--apply` repair semantics for `Z1xx` and `Z3xx` findings. Powered by the Deterministic Markdown Renderer. Implements an exact 3-Tier safety model:
  - **Tier 1 (Structural-safe auto-apply):** Safe transformations applied directly.
  - **Tier 2 (Proposal-only patch files):** Non-trivial fixes saved as patches for human review.
  - **Tier 3 (Security FATALs):** Security codes (`Z2xx`) which are explicitly banned from auto-fix.
- **Zenzic LSP (Language Server Protocol)** (Issue #12): A lightweight LSP implementation providing real-time IDE diagnostics and code-actions. Implements the JSON-RPC standard and hooks into the Auto-Fix engine to provide native IDE "Quick Fix" actions directly in the editor.

## Layer 3: Advanced Semantic Rules

*Deep-inspection rules utilizing the expanded AST Walker.*

- **Z108 STALE_ALLOWLIST_ENTRY** (Issue #70): Config-hygiene check for unused `absolute_path_allowlist` entries in `.zenzic.toml`. Implements config-parsing logic to cross-reference allowlist entries against the resolved file tree and detect unmatched absolute path exclusions.
- **Z407 BROKEN_CODE_REFERENCE:** Scan Markdown for backtick-quoted paths and verify their physical existence. **Implementation blocker:** Global RE2 heuristics generate false positives on hypothetical tutorial paths. The spec MUST mandate an explicit Markdown attribute opt-in (e.g., `` `src/main.py`{: .verify-path } ``) via the AST parser before this rule can be safely implemented.
- **Semantic Linting** (Issue #8): AST-based rules to detect semantically duplicate headings and empty/stub sections. Implements an AST state-machine required to track heading hierarchy and flag identical text content at the same tree depth.
- **Readability & Style Engine** (Issue #9): Integration of deterministic readability metrics (e.g., Flesch-Kincaid) and tone checks without relying on non-deterministic LLMs.
- **Smart Link Graph & Connectivity Analysis** (Issue #7): Build a directed graph of the documentation to detect unlinked pages (islands) and navigation cycles.

## Layer 4: Ecosystem & Interoperability

*Expanding the Zenzic perimeter to external frameworks and formats.*

- **The Bridge Architecture (TypeScript Docusaurus Plugin):** An official NPM plugin (`@zenzic/plugin-docusaurus`) that dumps a `.zenzic-vsm.json` artifact during the build, allowing the Python core to audit dynamic React/Webpack routes.
- **Community: Sphinx Adapter** (Issue #51): Support for parsing Sphinx `.rst` and `.md` documentation trees.
- **Community: Hugo Adapter** (Issue #50): Support for Hugo's specific `hugo.toml` configuration and frontmatter conventions.

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
