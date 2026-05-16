<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# Zenzic Roadmap

This document describes the planned milestone trajectory for Zenzic.
Dates are targets, not commitments. All milestones are subject to revision.

For the current release history, see [CHANGELOG.md](CHANGELOG.md).

---

## v0.8.x (current)

**Theme:** Tiered code governance, frozen security contracts, Sovereign Audit mode.

### Delivered in v0.8.0

- Tiered finding code model: Core (`Z1xx`), Structure (`Z4xx–Z5xx`), Governance (`Z6xx`),
  Security (`Z2xx`), and Infrastructure (`Z9xx`) bands.
- `FROZEN_CODES`, `NON_SUPPRESSIBLE_CODES`, `PLUGIN_FORBIDDEN_EXITS` — stable public
  contracts for integrators and plugin authors.
- `zenzic check all --audit`: Sovereign truth run bypassing all inline suppressions.
- `zenzic guard scan` / `zenzic guard init`: dedicated pre-commit credential guard
  powered by the credential scanner.
- RE2 DFA engine: O(n) guaranteed complexity for all pattern matching. Backreferences
  and lookaheads rejected at load time.
- `zenzic inspect codes`: live canonical code registry with tier, ownership, and
  non-suppressibility flag.
- Legacy migration map: `LEGACY_TO_CODE` for transparent `Z903→Z405`, `Z904→Z406`,
  `Z905→Z601`, `Z907→Z602` diagnostics.

### Planned for v0.8.x patch releases

- `Z109 STALE_ALLOWLIST_ENTRY`: config-hygiene check for unused `absolute_path_allowlist`
  entries (deferred from v0.7.1 to avoid Pillar 3 violation; requires dedicated
  `zenzic inspect config` command).
- `zenzic inspect config`: read-only config audit command.
- Windows CI matrix parity for all check commands.

---

## v0.9.x — Graphite (planned)

**Theme:** File integrity contracts, semantic schema validation, Plugin SDK.

### Planned

- **Z405 BROKEN_CODE_REFERENCE — File Integrity Check**: Zenzic will scan Markdown
  for backtick-quoted paths (e.g. `` `core/credentials.py` ``) and local file links,
  then verify their physical existence in the repository at scan time. Missing targets
  raise a Level 4 (Structure) finding. This eliminates "Phantom References" — stale
  code paths left behind after refactoring.

  > *Zenzic doesn't just check your links; it checks if your documentation knows
  > where your code lives.*

  Architectural note: the implementation extends `Resolver` with a new
  `resolve_code_reference(path: str) -> Finding | None` method, reusing the
  existing `_allowed_roots` boundary contract. No new subprocess calls.

- **Plugin SDK**: Stable AST adapter and rule APIs with semver guarantee.
  Exposure of the two-pass reference pipeline to external rule authors.
  Deprecation warnings for any v0.8 unstable API surfaces.
- **Semantic Schemas**: YAML/JSON frontmatter validation against declared schemas
  (e.g. `required_fields: [title, description]`). New finding tier `Z7xx`.
- **i18n schema parity**: Z907 extended to enforce frontmatter key parity between
  base and target language files (not just file existence).
- **Enhanced i18n Link Discovery (GAP-003)**: The Virtual Site Map (VSM) currently
  resolves links against the primary locale (EN). Translation files in `i18n/` that
  introduce links absent from their EN counterpart are not validated by Zenzic —
  only the Docusaurus build engine catches them at compile time. The planned fix
  extends the Docusaurus adapter to recurse into all locales declared in
  `docusaurus.config.ts` and cross-validate locale-specific links against the full
  multi-locale VSM. Structurally divergent links (present in IT but not EN) will
  raise a new `Z602 I18N_STRUCTURAL_DRIFT` finding. Identified in ADR-048 (v0.8.0
  cycle, Phase 40.2).
- **Configurable finding tiers**: allow projects to promote/demote finding severity
  via `[governance]` TOML section, with audit log of all overrides.

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

---

## Invariants (all milestones)

These constraints apply across every future release:

| Invariant | Description |
|-----------|-------------|
| Zero Subprocess | `subprocess.Popen` and `os.system` permanently banned from `src/`. |
| Pure Functions | The analysis engine has zero global state. |
| DFA Guarantee | All regex matching backed by RE2. O(n) complexity. |
| Exit Code Contract | Exit 2 = credential; Exit 3 = traversal. Never renumbered. |
| No Inference | Zero AI/ML runtime dependencies declared in `pyproject.toml`. |

---

Roadmap last updated: 2026-05-13
