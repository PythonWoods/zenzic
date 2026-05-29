<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

> **Development history (v0.1.0 – v0.8.0):** See the [Historical Archives](./changelogs/README.md).

## [Unreleased]

### Added

- Initial work on Plugin SDK architecture.
- **`--export-shields PATH`:** `zenzic score` can now write a [Shields.io](https://shields.io/endpoint)-compatible JSON endpoint to disk for dynamic CI badge telemetry. Upload the file to a GitHub Gist or `gh-pages` branch and embed `https://img.shields.io/endpoint?url=<raw_url>` in your README for a live quality badge.
- **Domain-Aware Discovery (`CODE_ASSET_SUFFIXES`):**** Source code files (`.py`, `.pyi`, `.ts`, `.tsx`, `.rs`, `.go`, and 20+ other code extensions) are now natively exempt from Z405 `UNUSED_ASSET` enforcement in `find_unused_assets`. Files are still indexed by the discovery engine for link resolution across the docs/source boundary. No configuration change is required.
- **Strict Local TOML Parsing:** `.zenzic.local.toml` now rejects unknown top-level keys with a fatal `ConfigurationError` (`LOCAL-TOML-STRICT`). Previously, unrecognised keys were silently discarded. Allowed sections: `core`, `build_context`, `project_metadata`, `governance`, `i18n`, `forbidden_patterns`, `secrets`, `debug`, `env`.

### Changed

- **Flat-cost suppression model (Breaking Change):** Every inline or per-file suppression now deducts exactly 1 point from the DQS regardless of `governance.suppression_cap`. Previously suppressions within the cap cost 0 points (allowance-based). `suppression_cap` now functions exclusively as a hard-fail threshold: exceeding it causes `zenzic score` to exit with code 1. Projects relying on the allowance model will see their maximum achievable score reduced by their suppression count.
- **`.zenzic.local.toml.example` eradicated (Phase 83):** The static template file has been deleted
  from all repositories. Use `zenzic init --local` to generate a fresh `.zenzic.local.toml`
  aligned to the current engine version.
- **`zenzic init --local` added (Phase 83):** New flag scaffolds only the machine-local overlay
  without touching the shared configuration. Ideal for contributors working in repos that already
  have `.zenzic.toml` committed.
- **`--dev` flag hard-removed from `zenzic init` (Phase 83):** The deprecated no-op flag has been
  deleted. Scripts invoking `zenzic init --dev` must be updated.
- **TOML templates hardened (Phase 83):** All three init templates (`.zenzic.toml`,
  `.zenzic.local.toml`, `[tool.zenzic]`) now expose every available configuration field with
  didactic comments. CI/CD snippet updated from `pipx` to `uvx`.
- **CLI decomposition (Phase 82 — Zero-Regression):** `_check.py` reduced from 1641 → 1478 lines
  by extracting four helpers into dedicated modules with backward-compatible re-exports:
  `_apply_per_file_ignores` and `_apply_directory_policies` moved to `_governance.py`;
  `_resolve_target` and `_apply_target` moved to the new `_target_resolver.py`;
  command-setup boilerplate consolidated in the new `_command_setup.py`.
  All 1550 tests pass unchanged.
- **Governance hardening — `brand_obsolescence` ADDITIVE merge:** `[governance].brand_obsolescence` in `.zenzic.local.toml` now uses additive semantics. Local terms extend the global list; they can never remove globally-configured protected terms. This prevents a non-versioned local override from silently disabling brand protection policy.
- **Z504 and Exit Code 4 relegated to Reserved/Inactive status:** `Z504 (QUALITY_REGRESSION)` and the corresponding exit code 4 emitted by `zenzic diff` have been removed from the public reference documentation. Both remain in the binary to preserve behavioral continuity but are no longer part of the documented exit-code contract, pending full differential analysis maturity.

### Fixed

- **SSoT `CodeDefinition` — Single Source of Truth for code metadata:** Severity, DQS penalty, and scoring category for every Z-code are now defined once in `codes.py` via `CODE_DEFINITIONS`. `scorer.py` derives `_CODE_PENALTY` and `_CODE_CATEGORY` from this structure at module init. `_check.py` derives finding severity via `_finding_severity()`. The `else "error"` catch-all is eliminated.
- **ADR-031 Paradox Resolution — Z103, Z111, Z113 onboarded to penalty table:** Z103 `ORPHAN_LINK` (−2.0 pts, Structural), Z111 `VIRTUAL_ROUTE_BROKEN` (−8.0 pts, Structural, equivalent to Z101 `LINK_BROKEN`), and Z113 `AUTHOR_KEY_COLLISION` (−2.0 pts, Structural) are now part of the DQS calculation. Previously these codes blocked `zenzic check links` (CI gate) while contributing zero DQS deduction (mathematical paradox).
- **Z114 CI gate bug fixed:** Z114 `LARGE_PAGINATION_SET` was erroneously classified as `severity="error"` by the `_check.py` catch-all despite being defined as `note` in `CODE_SARIF_LEVELS`. The SSoT migration corrects this: Z114 now correctly maps to `"info"` severity and does not trigger CI failure.
- **Security bypass fix — ADDITIVE deep merge for `excluded_dirs`, `excluded_file_patterns`, and `custom_rules` in `.zenzic.local.toml`:** All three keys were previously rejected by `LOCAL-TOML-STRICT`, making it impossible to use them in the machine-local overlay. They now use additive merge semantics: local values extend the global baseline and can never remove globally-configured entries. For `[[custom_rules]]`, a local rule sharing an `id` with a global rule overrides that single rule while leaving all other global rules intact. The allowed-keys list and the `LOCAL-TOML-STRICT` error message have been updated accordingly.
- **`zenzic init` MERGE SEMANTICS comment corrected:** The comment block generated by `zenzic init` in `.zenzic.local.toml` now correctly lists `brand_obsolescence`, `excluded_dirs`, `excluded_file_patterns`, and `custom_rules` as ADDITIVE, and correctly notes that `[governance]` is REPLACEMENT *except* for `brand_obsolescence`. The CI/CD snippet Python baseline has been corrected from `3.12` to `3.10`.
- **Enforced ADR-012 namespace contract — `custom_rules.id` must start with `ZZ-`:** Custom rule IDs are now validated at config load-time by a Pydantic field validator. Any `id` not starting with the strict uppercase prefix `ZZ-` (e.g. `Z101`, `zz-mycheck`) raises a `ConfigurationError` immediately, preventing namespace collision with Core finding codes and SARIF report pollution.

### Removed

- **Breaking change — `map_url()` and `classify_route()` removed from `BaseAdapter` protocol.** Custom adapters that implement these methods instead of `get_route_info()` must be updated. Migration: `adapter.map_url(rel)` → `adapter.get_route_info(rel).canonical_url`; `adapter.classify_route(rel, nav_paths)` → `adapter.get_route_info(rel).status`.
- **Breaking change — `find_orphans()` callback API removed.** The `classify_route` callback parameter is replaced by `adapter: BaseAdapter | None`.

---

## [0.8.0] — 2026-05-15 <!-- zenzic:ignore: Z601 release codename -->

### Added

- **Scoring Engine 2.0:** Mathematical quality assessment using tiered weights ($\omega_{tier}$) and Technical Debt penalties for suppressions ($\omega_{debt}$).
- **Integrity Regression Check (`zenzic diff`):** Command to compare documentation state between branches; exits with code 4 on quality regression.
- **Config Genealogy (`zenzic explain`):** Introspection command to trace rule origin (Default vs Global vs Local TOML).
- **Rule Z108 (EMPTY_LINK_TEXT):** New validator to detect links with empty or whitespace-only labels.
- **MDX-Native Suppressions:** Support for JSX comment syntax `{/* zenzic:ignore */}` alongside standard HTML comments.
- **Sovereign Audit Mode (`--audit`):** Global flag to bypass all suppressions for unfiltered repository inspection.
- **Privacy Gate (Z204):** Support for `.zenzic.local.toml` to enforce local-only forbidden patterns without repository leakage.
- **Core Hardening:** Native exclusion of system-critical files (`.zenzic.local.toml.example`, `*.sh`, `LICENSE`) from unused asset detection (Z405).

### Changed

- **Total Rebranding:** Eradication of theatrical terminology (Sentinel, Shield, Blood, Siege, Epoch, Forge) across source code, documentation, and CLI.
- **Execution Mode Normalization:** "Vanilla Mode" renamed to **"Standalone Mode"**.
- **Rule Z106 (CIRCULAR_LINK):** Downgraded to `info` severity; no longer penalizes the Quality Score.
- **CLI Output Standard:** Implemented "Ruff-style" UI with stderr-only headers and clean stdout for machine-readable payloads.
- **Namespace Finalization:** Formalized Tier Model (Z1xx–Z6xx) as the stable public API for violation codes.
- **Documentation Strategy:** Transitioned to "Agnostic Prose" (ADR-037); release codenames are treated exclusively as external identifiers.

### Fixed

- **Performance Optimization (ZRT-007):** Pre-compiled module-level RE2 patterns reduced regex overhead (N=10,000 links: 1.18s → 0.78s).
- **Z108 False Positives:** Implemented raw-line cross-validation to support inline code within reference link labels.
- **Z104 Resolution:** Eliminated false positives on infrastructure paths by standardizing GitHub Actions badges.
- **CLI Exception Handling:** Fixed `AttributeError` in `score/diff` path through structured link error API.

### Security

- **DFA-Pure Runtime:** Eradicated standard-library `re` module from production paths in favor of the RE2 Anti-Corruption Layer.
- **Z2xx Security Override:** Security findings (including Z204) now force a Quality Score of 0/100.

---

Looking for older versions? See [Historical Archives](./changelogs/README.md).
