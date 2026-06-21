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

## v0.8.x

**Theme:** Tiered code governance, frozen security contracts, Sovereign Audit mode.

---

## v0.9.x — Graphite

**Theme:** Governance Engine, DQS Suppression Audit, Tiered Penalty Model.

---

## v0.10.x — Magnetite

**Theme:** Native CI/CD Integration, Orthogonal Filtering, and Debt Eradication.

### Completed

- **Native CI/CD Integration**: Native support for `--ci`, `github-annotations` output format, and automatic header suppression.
- **Orthogonal Filtering**: Runtime filtering via `--only` for targeted, isolated gate checks.

### Planned (WIP)

- **Z407 BROKEN_CODE_REFERENCE — File Integrity Check**: Zenzic will scan Markdown
  for backtick-quoted paths (e.g. `` `core/credentials.py` ``) and local file links,
  then verify their physical existence in the repository at scan time. Missing targets
  raise a Level 4 (Structure) finding. This eliminates "Phantom References" — stale
  code paths left behind after refactoring.

  > *Zenzic doesn't just check your links; it checks if your documentation knows
  > where your code lives.*

  Architectural note: the implementation extends `Resolver` with a new
  `resolve_code_reference(path: str) -> Finding | None` method, reusing the
  existing `_allowed_roots` boundary contract. No new subprocess calls.

- **Dead Suppression Elimination (Z603)**: Detects inline `zenzic:ignore` directives
  that do not correspond to any active finding. Prevents projects from accumulating
  "phantom debt" — paying the 1-point DQS penalty for a suppression no longer needed
  due to code fixes or configuration changes. Analogous to Ruff `RUF100` and ESLint
  `--report-unused-disable-directives`. Implementation requires extending the
  suppression engine (`suppressions.py`) to track which inline tags are consumed
  during the scan lifecycle, then emitting a new `Z603` finding for unclaimed tags.

- **Docusaurus Cross-Instance Resolver**: Upgrade `_docusaurus.py` to natively resolve
  root-relative links (e.g., `/developers/page`) across multiple plugin instances,
  eliminating the need for Z105 suppressions on inter-plugin routing. This includes
  locale-aware prefix resolution (e.g., `/it/developers/`) so that translated pages
  can link to sibling plugin instances without triggering Z105. Identified as a
  structural gap when auditing `zenzic-doc`: Docusaurus rejects `../` relative paths
  across plugin boundaries, forcing authors to use absolute URLs and manual
  suppressions.

---

## v0.11.x — Monorepo & DX (current)

**Theme:** File integrity contracts, semantic schema validation, Plugin SDK, config hygiene.

### Completed

- **Monorepo Scalability**: Dynamic root resolution for Docusaurus (`docusaurus_site_root`), allowing Zenzic to operate seamlessly in nested `website/` architectures.
- **Path-Aware Exclusion Engine**: Upgraded `excluded_dirs` to support `.gitignore` slash semantics, enabling strictly repo_root-relative targeting without false positives.
- **Python 3.12+ RE2 Parity**: Custom `translate_glob_to_re2` implementation, eradicating `fnmatch` atomic group crashes and preserving DFA linear-time guarantees.
- **DX Redesign**: Implementation of a visual progress bar and mathematical transparency via the `--breakdown` flag for DQS scoring.

### Planned

- `Z108 STALE_ALLOWLIST_ENTRY` (Issue #70): config-hygiene check for unused `absolute_path_allowlist`
  entries (deferred from the v0.7.x cycle to avoid Pillar 3 violation; requires
  `zenzic config` command).
- Windows CI matrix parity for all check commands.

- **Logic Site Map (LSM) — Documentation Topology Simplification**: The zenzic-doc
  documentation corpus undergoes a formal deduplication pass following the Logic
  Site Map protocol. Duplicate conceptual coverage (scoring, configuration reference,
  ecosystem) is consolidated into canonical master pages; zombie files and superseded
  ADRs are purged. Target: ≥30% reduction in total page count, 100% retention of
  information fidelity.

- **Plugin SDK** *(WIP)*: Stable AST adapter and rule APIs with semver guarantee.
  Exposure of the two-pass reference pipeline to external rule authors.
  Deprecation warnings for any v0.9 unstable API surfaces.
- **Semantic Schemas**: YAML/JSON frontmatter validation against declared schemas
  (e.g. `required_fields: [title, description]`). New finding tier `Z7xx`.
- ~~**i18n schema parity (Z907)**~~ — **CANCELLED (ADR-034):** The Z602/Z907 I18N_PARITY scanner was eradicated in v0.14.0. Bilingual parity enforcement is deferred to future adapter plugins and will not be implemented in the core engine.
- **Configurable finding tiers**: allow projects to promote/demote finding severity
  via `[governance]` TOML section, with audit log of all overrides.

---

## v0.12.0 — The Static Purity Pivot (planned)

**Strategic Focus:** Deepen native support for Pure Static Engines (MkDocs, Sphinx, Hugo) where AST parsing guarantees 100% deterministic accuracy without bundler interference.

### The Great Migration

Tactical Bridge: zenzic-doc migrated to MkDocs Material and then to Zensical — completed in v0.13.0. ADR-020 (Mirror Law) has been deprecated; Zenzic is now English-Only.

---

## v0.14.0 — The Great Eradication (in progress)

**Theme:** Surgical removal of dead weight. Zero accumulation of inactive code paths.

### Delivered

- **Z602 I18N_PARITY Engine Eradicated (ADR-034):** `find_i18n_parity()` and 443 lines of bilingual scanner logic removed from the core. Z602 remains in the code namespace as `status="inactive"` for config forward-compatibility. `I18nConfig`/`I18nSource` models removed from `zenzic.models.config`.
- **`LEGACY_TO_CODE` Deleted:** The `Z9xx → Zxxx` migration alias dictionary removed. All canonical code references updated.
- **CodeDefinition.status field:** `NamedTuple` gains a `status: str = "active"` field. INACTIVE codes render as dim in `inspect codes`.
- **Z506 MALFORMED_FRONTMATTER:** New built-in always-active rule that detects malformed YAML frontmatter opening delimiters on line 1. Severity `error`, −5.0 pts (Content). Gallery page and finding-codes reference updated.
- **Breaking Changes:** Full list in CHANGELOG.md under `## [0.14.0]`.

---

## v0.15.0 — Semantic Validation (planned)

### Planned

- **Semantic Metadata Cross-Validation (Z507)**: Native support for cross-referencing Markdown frontmatter entities against framework-specific metadata files (e.g., verifying authors in MkDocs against .authors.yml). This extends Zenzic's capability from pure Markdown AST analysis into framework-aware semantic validation.

---

## v1.0.0 — Graphite LTS (planned)

**Theme:** Long-Term Support release. Stability, portability, and production confidence.

### Goals

- **API freeze**: all public symbols in `zenzic.rules`, `zenzic.models`, and
  `zenzic.core.adapters` enter semver-stable contracts. No breaking changes without
  a major version bump.
- **Full Windows parity**: all features (including `signal`-based canary watchdog
  replacement) validated on Windows Server and GitHub Actions Windows runners.
- **REUSE 4.x compliance**: migrate to REUSE 4.x specification when stable.
- **Formal test coverage floor**: 85%+ branch coverage enforced in CI across all
  three supported Python versions (current floor: 80%+ line coverage).
- **Certified plugin ecosystem**: a curated registry of community plugins that meet
  the Plugin SDK contract.
- **Determinism audit**: formal proof-of-determinism report published for all
  Core (`Z1xx`) and Security (`Z2xx`) finding codes.
- **Auto-Fix Engine (`zenzic fix`)**: semantic `--dry-run` / `--apply` repair
  semantics for Z1xx and Z3xx findings. `zenzic fix` never modifies Z2xx
  (Security) findings — those require human review. Implementation is pure Python
  with zero subprocess calls (Pillar 2 invariant). Status: design phase; no code
  merged. Identified as GAP-001 in the Technical Debt Ledger.
- **Readability & Style Engine (Issue #9)**: Integrate pure readability metrics (Flesch-Kincaid) and style checks tailored for technical documentation.
- **Semantic Linting (Issue #8)**: Implement AST-based rules to detect semantically duplicate headings, empty sections, and inconsistent heading jumps.
- **Smart Link Graph & Connectivity Analysis (Issue #7)**: Build a directed graph of the documentation to detect unlinked pages and navigation cycles.

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

Roadmap last updated: 2026-06-11
