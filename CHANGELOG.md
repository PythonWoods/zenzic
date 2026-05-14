<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

> **Development history (v0.1.0 – v0.7.1):** See the [Historical Archives](./changelogs/README.md).

## [Unreleased]

### Added

- Initial work on Plugin SDK architecture.

---

## [0.8.0] — 2026-05-12 <!-- zenzic:ignore: Z601 historical release codename -->

### Added

- **Scoring Engine 2.0:** Implemented mathematical quality assessment using
  tiered weights and Technical Debt penalties.
- **Integrity Regression Check (`zenzic diff`):** New command to compare
  documentation state between branches; exits with code 4 on quality
  regression.
- **Config Genealogy (`zenzic explain`):** New introspection command to trace
  the origin and priority of active rules.
- **Audit Mode (`--audit`):** Global flag to bypass all suppressions
  (`zenzic:ignore`) for unfiltered repository inspection.
- **Core Hardening:** Native exclusion of system-critical files
  (`.zenzic.local.toml.example`, `*.sh`, `LICENSE`) from unused asset
  detection (Z405).
- **CLI Metadata Registry:** Centralized command definitions in `_metadata.py`
  and unified app factory (`create_app`) for consistent CLI behavior.
- **Privacy Gate (Z204):** Support for `.zenzic.local.toml` to enforce
  local-only forbidden patterns without repository leakage.
- **Stability Contract constants in `codes.py`:** Added `FROZEN_CODES`,
  `NON_SUPPRESSIBLE_CODES`, and `PLUGIN_FORBIDDEN_EXITS` as immutable public
  contract surfaces.
- **Tier model formalized in the public registry:** Core/Structure/Governance
  ownership is explicit in canonical code mappings.
- **Legacy migration map for diagnostics:** Added `LEGACY_TO_CODE` to map
  `Z903`→`Z405`, `Z904`→`Z406`, `Z905`→`Z601`, `Z907`→`Z602`.
- **ADR-013 (Regex ACL) published in developer docs (EN/IT):** Formalizes the
  anti-corruption regex facade strategy and strict RE2 enforcement.

### Changed

- **Total Rebranding:** Eradication of theatrical terminology across source
  code, documentation, and CLI.
- **Execution Mode Normalization:** "Vanilla Mode" renamed to
  **"Standalone Mode"**.
- **CLI Output Standard:** Implemented "Ruff-style" UI with stderr-only headers
  and clean stdout for machine-readable payloads (JSON/SARIF).
- **Namespace Finalization:** Formalized Tier Model (Z1xx–Z6xx) as the stable
  public API for violation codes; runtime/docs/examples now use canonical IDs
  (`Z405`, `Z406`, `Z601`, `Z602`) while preserving legacy anchors only for
  migration diagnostics.
- **Documentation Strategy:** Transitioned to "Agnostic Prose" (ADR-037);
  release codenames are now treated as external identifiers only.
- **`--strict` policy normalized in `check`, `score`, and `diff`:** strict mode
  is now documented and handled as warning-promotion to fatal exit policy.
- **Reporter footer contract modularized:** `ZenzicReporter.render()` now
  accepts caller-provided `FooterNotice`; command-specific navigation hints are
  emitted by callers instead of hardcoded in the report engine.

### Fixed

- **Performance Optimization (ZRT-007):** Pre-compiled module-level RE2
  patterns reduced regex overhead in large-scale scans (N=10,000 links:
  1.18s → 0.78s).
- **Z000 Registry Gap:** Added `UNSUPPORTED_ENGINE` to `CODE_NAMES`,
  `CODE_DESCRIPTIONS`, and `CODE_SARIF_LEVELS`; canonical registry and
  documentation encyclopedia are now aligned.
- **Link Resolution:** Fixed Z104 false positives on infrastructure paths by
  implementing badge-standard for GitHub Actions.
- **Header channel split hardened:** command headers are emitted via stderr UI,
  preserving clean stdout payloads for machine-readable flows.

### Security

- **DFA-Pure Runtime:** Completed removal of standard-library `re` module from
  production paths in favor of the RE2 Anti-Corruption Layer; unsupported
  constructs now fail explicitly instead of silently degrading to stdlib regex.
- **Z204 Criticality:** Security findings now force a Quality Score of 0/100,
  bypassing standard weight calculations.
- **Lint gate for regex engine policy:** Ruff banned API guard prevents
  reintroduction of direct `re` imports in protected source surfaces.

---

Looking for older versions? See [Historical Archives](./changelogs/README.md).
