<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

> **Development history (v0.1.0 – v0.7.1):** See the [Changelog Archive](CHANGELOG.archive.md).

## [Unreleased]

### Added

- **Epoch 8 decree:** "Epoch 8: Basalt – The Sovereign Transition. Introducing Suppression CAP, Local Sanctuary, and Avion-Grade Governance."
- **Phase 2 (The Truth-Seeker) delivered:** Added Sovereign Audit mode via
  `zenzic check all --audit` (bypasses inline `zenzic-ignore` and
  `[governance].per_file_ignores` for suppressible findings), plus native
  Secret Guard commands (`zenzic guard scan`, `zenzic guard init`) powered by
  Shield signatures for pre-commit enforcement.
- **Stability Contract constants in `codes.py`:** Added `FROZEN_CODES`,
  `NON_SUPPRESSIBLE_CODES`, and `PLUGIN_FORBIDDEN_EXITS` as immutable public
  contract surfaces for v0.8.0 Basalt.
- **Tier model formalized in the public registry:** Core/Structure/Governance
  ownership is explicit in canonical code mappings.
- **Legacy migration map for diagnostics:** Added `LEGACY_TO_CODE` to map
  `Z903`→`Z405`, `Z904`→`Z406`, `Z905`→`Z601`, `Z907`→`Z602`.
- **ADR-013 (Regex ACL) published in developer docs (EN/IT):** Formalizes the
  anti-corruption regex facade strategy and strict RE2 enforcement.
- **DX release guardrails:** Added `_check-hooks`, `version`,
  `release-dry --short`, and `release-contracts` recipes to standardize local
  release preflight.

### Changed

- **ADR-012 namespace contract finalized for v0.8.0:** Runtime/docs/examples now
  use canonical IDs (`Z405`, `Z406`, `Z601`, `Z602`) while preserving legacy
  anchors only for migration diagnostics.
- **Boundary-testing CI parity:** Nox `PYTHONS` aligned to floor/peak
  (`3.10`, `3.14`) and fixed-version sessions pinned to `3.14`.
- **Mypy compatibility floor aligned to runtime floor:**
  `[tool.mypy] python_version = "3.10"`.

### Fixed

- **Registry parity gap closed for `Z000` (`UNSUPPORTED_ENGINE`):** Added to
  `CODE_NAMES`, `CODE_DESCRIPTIONS`, and `CODE_SARIF_LEVELS`; canonical
  registry and docs encyclopedia are now aligned.

### Security

- **ZRT-007 hardening completed in production source:** Standard-library `re`
  usage removed from runtime paths in favor of the RE2-backed ACL facade.
- **No-fallback regex policy enforced:** Unsupported constructs now fail
  explicitly under RE2 instead of silently degrading to stdlib regex runtime.
- **Lint gate for regex engine policy:** Ruff banned API guard prevents
  reintroduction of direct `re` imports in protected source surfaces.

---
