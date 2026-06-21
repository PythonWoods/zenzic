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

## v0.14.0 (current)

**Theme:** Surgical removal of dead weight. Zero accumulation of inactive code paths.

### Delivered

- **Zensical Migration & Docusaurus Eradication:** Complete architectural pivot to pure Markdown statics, purging legacy React AST dependencies.
- **RE2 Enforcement:** Python 3.12+ RE2 parity with linear-time guarantees.
- **TOML Strict Validation:** Path-aware exclusion engine and strict configuration hygiene.
- **Z506 MALFORMED_FRONTMATTER:** Native built-in rule detecting malformed YAML frontmatter boundaries.

---

## v0.15.0 (planned)

**Theme:** Semantic Validation & Developer Experience.

### Planned Features

- **The Auto-Fix Engine (`zenzic fix`)**: Semantic `--dry-run` / `--apply` repair semantics for Z1xx and Z3xx findings.
- **Custom Rules API v2 (AST Walker)**: Stable AST adapter and rule APIs with semver guarantee. Exposure of the two-pass reference pipeline to external rule authors.
- **Z507 AUTHOR_NOT_FOUND**: Native support for cross-referencing Markdown frontmatter entities against framework-specific metadata files.
- **The Bridge Architecture (TypeScript Docusaurus Plugin)**: Official plugin interface to support edge-case runtime frameworks outside the core engine.
- **Z108 STALE_ALLOWLIST_ENTRY**: Config-hygiene check for unused `absolute_path_allowlist` entries.
- **Semantic Schemas Validation**: YAML/JSON frontmatter validation against declared schemas (e.g. `required_fields: [title, description]`).
- **Z407 BROKEN_CODE_REFERENCE**: Scan Markdown for backtick-quoted paths and verify their physical existence.
- **Dead Suppression Elimination (Z603)**: Detects inline `zenzic:ignore` directives that do not correspond to any active finding.
- **Configurable Finding Tiers**: Allow projects to promote/demote finding severity via `[governance]` TOML section.
- **Readability & Style Engine**: Integrate pure readability metrics (Flesch-Kincaid) and style checks.
- **Semantic Linting**: Implement AST-based rules to detect semantically duplicate headings and empty sections.
- **Smart Link Graph & Connectivity Analysis**: Build a directed graph of the documentation to detect unlinked pages and navigation cycles.

---

## v1.0.0 — Graphite LTS (planned)

**Theme:** Long-Term Support release. Stability, portability, and production confidence.

### Goals

- **API freeze**: all public symbols in `zenzic.rules`, `zenzic.models`, and `zenzic.core.adapters` enter semver-stable contracts. No breaking changes without a major version bump.
- **Full Windows parity**: all features (including `signal`-based canary watchdog replacement) validated on Windows Server and GitHub Actions Windows runners.
- **REUSE 4.x compliance**: migrate to REUSE 4.x specification when stable.
- **Formal test coverage floor**: 85%+ branch coverage enforced in CI across all three supported Python versions.
- **Certified plugin ecosystem**: a curated registry of community plugins that meet the Plugin SDK contract.
- **Determinism audit**: formal proof-of-determinism report published for all Core (`Z1xx`) and Security (`Z2xx`) finding codes.

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

Roadmap last updated: 2026-06-21
