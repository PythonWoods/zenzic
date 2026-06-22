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

## Horizon 1: Current Focus (Now)

(Items actively being worked on or immediately next).

- **The Bridge Architecture** (TypeScript Docusaurus Plugin)
- **Custom Rules API v2** (AST Walker)
- **Configuration Hygiene: Z108 STALE_ALLOWLIST_ENTRY** (Issue #70)

---

## Horizon 2: Core Expansion (Next)

(Major engine capabilities and auto-remediation).

- **Deterministic Auto-Fix Engine (`zenzic fix`)** (Issue #10)
- **Deterministic Markdown Renderer** (Issue #11)
- **Semantic Schemas Validation** (YAML/JSON frontmatter schemas)
- **Z407 BROKEN_CODE_REFERENCE** (Pending explicit AST opt-in via Markdown attributes)

---

## Horizon 3: Ecosystem & Advanced Analysis (Later)

(Integrations and deep semantic checks).

- **Zenzic LSP (Language Server Protocol)** (Issue #12)
- **Semantic Linting & Duplicate Headings** (Issue #8)
- **Readability & Style Engine** (Issue #9)
- **Smart Link Graph & Connectivity Analysis** (Issue #7)
- **Community: Sphinx Adapter** (Issue #51)
- **Community: Hugo Adapter** (Issue #50)

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
