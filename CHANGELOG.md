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

- **`"lock"` emoji registered in `_EMOJI`:** `emoji('lock')` now resolves to
  🔒 in the emoji registry (`zenzic.core.ui`); was silently rendering the
  literal string `"lock"`.
- **UI/Rich output conventions in CONTRIBUTING.md:** Documented the compact
  (Ruff-style) vertical spacing rule, `ZenzicPalette.DIM` mandate, and emoji
  registration requirement.

### Changed

- **Chromatic DRY compliance — all raw `[dim]` replaced with
  `ZenzicPalette.DIM`** across the entire `src/` tree: `reporter.py`, `ui.py`,
  `main.py`, `cli/_shared.py`, `cli/_clean.py`, `cli/_guard.py`,
  `cli/_check.py`, `cli/_inspect.py`, `cli/_standalone.py`, `cli/_lab.py`,
  `models/config.py`. `ZenzicPalette.DIM` (#64748b Slate) is now the sole
  chromatic authority for secondary/dim text. Added `ZenzicPalette` import to
  `models/config.py`.
- **Compact footer spacing (Ruff-style):** Removed the spurious blank line
  before `Try 'zenzic check --help'` in the findings path (`reporter.py`),
  aligning the findings footer layout with the all-clear footer layout.
- **Issue template bonifica:** Replaced "Blood Sentinel / Shield" with
  "Z201 Credential Scanner / Path Traversal Gate" in
  `gate-bypass-postmortem.md`.
- **Deprecated "Sentinel" terms removed** from `.pre-commit-hooks.yaml`
  (`Sentinel gate` → `quality gate`) and GitHub issue templates
  (`bug_report.yml`, `security_vulnerability.yml`).

### Fixed

- **Double icon `✨ ✓ Analysis complete:`** removed — the `✓` was redundant
  with the sparkles emoji; both all-clear paths in `reporter.py` corrected.
- **Leading space before 💡 in the no-external notice** removed: the
  `[dim] 💡...` string had a leading space that produced misaligned output.
- **Trailing `\n` in no-external notice** removed, which was causing a spurious
  blank line before the Suppression Audit footer.
- **Spurious blank line before `🔒 Suppression Audit`** removed from
  `print_suppression_audit_footer()` in `cli/_governance.py`.

---

## [0.8.0] — 2026-05-11

### Added

- **Phase 2 (The Truth-Seeker) delivered:** Added Sovereign Audit mode via
  `zenzic check all --audit` (bypasses inline `zenzic-ignore` and
  `[governance].per_file_ignores` for suppressible findings), plus native
  Secret Guard commands (`zenzic guard scan`, `zenzic guard init`) powered by
  Credential Scanner signatures for pre-commit enforcement.
- **Stability Contract constants in `codes.py`:** Added `FROZEN_CODES`,
  `NON_SUPPRESSIBLE_CODES`, and `PLUGIN_FORBIDDEN_EXITS` as immutable public
  contract surfaces for v0.8.0 Basalt.<!-- zenzic-ignore: Z601 - release codename -->
- **Tier model formalized in the public registry:** Core/Structure/Governance
  ownership is explicit in canonical code mappings.
- **Legacy migration map for diagnostics:** Added `LEGACY_TO_CODE` to map
  `Z903`→`Z405`, `Z904`→`Z406`, `Z905`→`Z601`, `Z907`→`Z602`.
- **ADR-013 (Regex ACL) published in developer docs (EN/IT):** Formalizes the
  anti-corruption regex facade strategy and strict RE2 enforcement.

### Changed

- **ADR-012 namespace contract finalized for v0.8.0:** Runtime/docs/examples now
  use canonical IDs (`Z405`, `Z406`, `Z601`, `Z602`) while preserving legacy
  anchors only for migration diagnostics.

### Fixed

- **Registry parity gap closed for `Z000` (`UNSUPPORTED_ENGINE`):** Added to
  `CODE_NAMES`, `CODE_DESCRIPTIONS`, and `CODE_SARIF_LEVELS`; canonical
  registry and docs encyclopedia are now aligned.
- **Performance regression in `VSMBrokenLinkRule.check_vsm` fixed (ZRT-007
  implementation):** The `zenzic.core.regex` RE2 facade has no internal pattern
  cache; every `re.sub/search` call with a raw string literal recompiled the
  pattern from scratch. 12 inline call-sites across 5 source files
  (`rules.py`, `validator.py`, `scanner.py`, `adapters/_docusaurus.py`,
  `adapters/_utils.py`, `cli/_standalone.py`) replaced with 11 pre-compiled
  module-level constants. Added fast path in `_to_canonical_url` for plain
  relative hrefs. `TestAdaptiveRuleEngineTortureTest` (N=10 000 links):
  `1.18 s → 0.78 s` (threshold < 1.0 s). All 1 500 tests pass.

### Security

- **ZRT-007 hardening completed in production source:** Standard-library `re`
  usage removed from runtime paths in favor of the RE2-backed ACL facade.
- **No-fallback regex policy enforced:** Unsupported constructs now fail
  explicitly under RE2 instead of silently degrading to stdlib regex runtime.
- **Lint gate for regex engine policy:** Ruff banned API guard prevents
  reintroduction of direct `re` imports in protected source surfaces.

---

Looking for older versions? See [Historical Archives](./changelogs/README.md).
