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
