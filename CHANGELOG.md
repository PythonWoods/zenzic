<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.4.0-rc2] — 2026-03-28 — The Great Decoupling

> **Sprint 6.** Zenzic ceases to own its adapters. Third-party adapters install as Python
> packages and are discovered at runtime via entry-points. The Core never imports a concrete
> adapter again. Also promotes the documentation from a collection of pages to a structured
> knowledge base with i18n parity.

### Added

- **`zenzic clean assets` command** — New interactive autofix command that automatically deletes unused images and assets from the repository. By default, it prompts `[y/N]` for safety. Supports `-y` / `--yes` for CI/CD automation. Can be run safely after `zenzic check assets`.
- **Dynamic Adapter Discovery** (`_factory.py`) — `get_adapter()` no longer imports
  `MkDocsAdapter` or `ZensicalAdapter` directly. The factory queries
  `importlib.metadata.entry_points(group="zenzic.adapters")` at runtime. Installing a package
  that registers itself under this group makes it immediately available as `--engine <name>`;
  no Zenzic release required. Built-in adapters (`mkdocs`, `zensical`, `vanilla`) are
  registered in `pyproject.toml`:

  ```toml
  [project.entry-points."zenzic.adapters"]
  mkdocs   = "zenzic.core.adapters:MkDocsAdapter"
  zensical = "zenzic.core.adapters:ZensicalAdapter"
  vanilla  = "zenzic.core.adapters:VanillaAdapter"
  ```

- **`from_repo()` classmethod pattern** — Adapters own their own config loading and
  enforcement contract. The factory calls `AdapterClass.from_repo(context, docs_root,
  repo_root)` when present, falling back to `__init__(context, docs_root)` for
  backwards-compatible adapters.

- **`has_engine_config()` protocol method** (`BaseAdapter`) — Replaces the previous
  `isinstance(adapter, VanillaAdapter)` check in `scanner.py`. The scanner is now fully
  decoupled from all concrete adapter types; it only imports `get_adapter` and speaks the
  `BaseAdapter` protocol.

- **`list_adapter_engines() -> list[str]`** — Public function returning the sorted list of
  registered adapter engine names. Used by the CLI `--engine` validation path.

- **`--engine ENGINE` flag on `check orphans` and `check all`** — Overrides
  `build_context.engine` for a single run without modifying `zenzic.toml`. Validated
  dynamically against installed adapters; unknown names produce a friendly error listing
  available choices:

  ```text
  ERROR: Unknown engine adapter 'hugo'.
  Installed adapters: mkdocs, vanilla, zensical
  Install a third-party adapter or choose from the list above.
  ```

- **`[[custom_rules]]` DSL** — Project-specific lint rules declared in `zenzic.toml` as
  a pure-TOML array-of-tables. Each rule applies a compiled regular expression line-by-line
  to every `.md` file. Rules are adapter-independent: they fire identically with `mkdocs`,
  `zensical`, and `vanilla` adapters. Patterns are compiled once at config-load time.
  Invalid regex patterns raise `ConfigurationError` at startup. Fields: `id` (required),
  `pattern` (required), `message` (required), `severity` (`"error"` | `"warning"` | `"info"`,
  default `"error"`). See [Custom Rules DSL](docs/configuration/custom-rules-dsl.md).

- **`ZensicalAdapter.from_repo()` enforcement contract** — When `engine = "zensical"` is
  declared, `zensical.toml` **must** exist at the repository root. `from_repo()` raises
  `ConfigurationError` immediately if it is absent. No silent fallback to `mkdocs.yml`.

- **`MkDocsAdapter.config_file_found` tracking** — `from_repo()` records whether
  `mkdocs.yml` was actually found on disk (independently of whether it parsed successfully).
  `has_engine_config()` returns `True` when the file existed, allowing orphan detection to
  run even when the YAML is malformed.

- **`zenzic init` command** — Scaffolds a `zenzic.toml` at the repository root with smart
  engine discovery. Detects `mkdocs.yml` → pre-sets `engine = "mkdocs"`; detects
  `zensical.toml` → pre-sets `engine = "zensical"`; no engine config found → Vanilla
  scaffold. All settings are commented out by default. `--force` overwrites an existing file.

- **UX Helpful Hint panel** — When any `check` command runs without a `zenzic.toml`, Zenzic
  prints an informational Rich panel guiding the user to `zenzic init`. The hint is suppressed
  automatically once `zenzic.toml` exists. Driven by the new `loaded_from_file: bool` flag
  returned by `ZenzicConfig.load()`.

- **`ZenzicConfig.load()` returns `tuple[ZenzicConfig, bool]`** — The second element
  (`loaded_from_file`) is `True` when `zenzic.toml` was found and parsed, `False` when
  built-in defaults are in use. Callers in `cli.py`, `plugin.py`, `scanner.py`, and
  `validator.py` updated accordingly.

- **Documentation — Configuration split** — `configuration.md` de-densified into a
  three-page reference under `docs/configuration/`:
  [Overview](docs/configuration/index.md) ·
  [Core Settings](docs/configuration/core-settings.md) ·
  [Adapters & Engine](docs/configuration/adapters-config.md) ·
  [Custom Rules DSL](docs/configuration/custom-rules-dsl.md)

- **Documentation — Italian parity** — `docs/it/` now mirrors the full English structure:
  `it/configuration/` (4 pages), `it/developers/writing-an-adapter.md`,
  `it/guides/migration.md`.

- **Documentation — Writing an Adapter guide** (`docs/developers/writing-an-adapter.md`) —
  Full protocol reference: `BaseAdapter` methods, `from_repo` pattern, entry-point
  registration, test utilities (`RepoBuilder`, `assert_no_findings`, protocol compliance
  checker).

- **Documentation — MkDocs → Zensical migration guide** (`docs/guides/migration.md`) —
  Four-phase migration workflow: establish baseline → switch binary → declare identity →
  verify link integrity. Includes `[[custom_rules]]` portability note and quick-reference
  table.

### Changed

- **Unknown engine → `VanillaAdapter`** (breaking from v0.3 behaviour) — Previously, an
  unknown `engine` string caused a fallback to `MkDocsAdapter`. Now it falls back to
  `VanillaAdapter` (no-op orphan check), consistent with "no registered adapter = no
  engine-specific knowledge".

- **`scanner.py` is now protocol-only** — removed `VanillaAdapter` import; replaced
  `isinstance(adapter, VanillaAdapter)` with `not adapter.has_engine_config()`. The scanner
  has zero dependency on any concrete adapter class.

- **`output_format` parameter** (was `format`) — Renamed in `check_all`, `score`, and
  `diff` CLI commands to avoid shadowing the Python built-in `format`. Affects programmatic
  callers using the internal `_collect_all_results` API; the `--format` CLI flag is unchanged.

### Fixed (Sprint 6 — v0.4.0-rc2)

- **`check all` now runs 7/7 checks** — The reference integrity pipeline
  (`scan_docs_references_with_links`) was never invoked by `check all`. Dangling references
  and Shield events could pass the global gate silently. Fixed: `_collect_all_results` now
  calls the reference pipeline. `_AllCheckResults` gains `reference_errors` and
  `security_events` fields. Shield exit code `2` is enforced unconditionally. JSON output
  gains a `"references"` key.

- **Stale `docs/it/configuration.md` ghost file** — The Italian configuration god-page was
  never deleted after the configuration split into `docs/it/configuration/`. The orphan
  checker correctly skips locale subtrees by design; the file was a physical ghost.
  Fix: file deleted.

- **`rule_findings` silently discarded in `check references`** — `IntegrityReport.rule_findings`
  was populated by the scanner but never iterated in the `check references` CLI output loop.
  Custom rule violations were invisible to users. Fixed by adding iteration over
  `report.rule_findings` in the output path.

### Fixed (Sprint 5 — v0.4.0-rc1)

- **`find_repo_root()` root marker** — changed from `mkdocs.yml` to `.git` or `zenzic.toml`.
  Zenzic no longer requires an MkDocs configuration file to locate the repository root.
  Engine-agnostic by design.

- **O(N) reads** — `scan_docs_references_with_links` previously read each file twice (Phase A
  harvest + Phase B link registration). New `_scan_single_file()` helper returns
  `(IntegrityReport, ReferenceScanner | None)` and reuses the scanner object for URL
  registration, eliminating the double-read bottleneck.

- **`[[custom_rules]]` regex pre-compilation** — `placeholder_patterns_compiled` field added
  to `ZenzicConfig` via `model_post_init`. Patterns are compiled once at config-load time
  via `model_post_init`, not per-file during scanning.

- **YAML frontmatter skipping** — `_iter_content_lines()` now skips the leading `---` YAML
  frontmatter block. Previously, frontmatter was passed to the Shield and placeholder scanner,
  causing false `SECRET` and `placeholder-text` findings on pages with valid frontmatter values
  that happened to match credential or stub patterns.

- **Image reference false positives** — `_RE_REF_LINK` regex now includes a `(?<!!)` negative
  lookbehind. Image references (`![alt][id]`) no longer generate false `DANGLING_REFERENCE`
  findings; group indices updated to `(1=full, 2=text, 3=ref_id)`.

- **Shield prose scanning** — `scan_line_for_secrets` integrated into the `harvest()` loop
  on non-definition lines (defence-in-depth). Credentials embedded in prose — not just in
  reference URLs — are now detected during Pass 1. No duplicate `SECRET` events.

- **Percent-encoded asset filenames** — `check_asset_references()` applies `unquote()` to
  decoded URL paths before `normpath`. Filenames like `logo%20v2.png` are now correctly
  matched against the filesystem and do not generate false "unused asset" findings.

- **`subprocess` import isolation** — moved inside `serve()` body; no longer pollutes the
  CLI module namespace at import time.

### Security

- **Shield-as-firewall in prose** (CVE-2026-4539 hardening) — The credential scanner now
  runs on every non-definition line during Pass 1, not only on reference URL values. A
  credential copied into a Markdown paragraph rather than a reference link is caught before
  any URL validation or HTTP request is issued. Exit code `2` remains reserved exclusively
  for Shield events and cannot be suppressed by any flag.

### Tests

- `test_vanilla_mode.py::test_get_adapter_unknown_engine_falls_back_to_vanilla` updated —
  unknown engine now correctly returns `VanillaAdapter` (was `MkDocsAdapter`).
- `test_rules.py` — added parametrized cross-adapter test verifying `[[custom_rules]]` fire
  identically for `mkdocs`, `zensical`, and `auto` engines.
- **435 tests pass.** `zenzic check all` — 7/7 OK on the project's own documentation
  (self-dogfood, full i18n parity verified).

---

## [0.4.0-rc1] — 2026-03-27 — The RC1 Hardening Sprint

> **Sprint 5.** Eleven production-grade fixes applied to `0.4.0-alpha.1`. Engine-agnostic
> root discovery, O(N) read budget, frontmatter skip, Shield prose scanning, image-ref
> false-positive elimination.

### Added

- **`validate_same_page_anchors`** — new `zenzic.toml` boolean field (default `false`). When
  enabled, same-page anchor links (`[text](#section)`) are validated against the ATX headings
  extracted from the source file. Disabled by default because anchor IDs can also originate
  from HTML attributes, plugins, or build-time macros invisible at source-scan time.
- **`excluded_external_urls`** — new `zenzic.toml` list field (default `[]`). URL prefixes
  listed here are skipped by the external broken-link checker. Prefix-based matching: a single
  entry covers an entire domain or repository subtree.
- **Community section** — new documentation section: Get Involved, FAQs, Contributing guide,
  Report a Bug, Docs Issue, Request a Change, Pull Requests.
- **`excluded_build_artifacts`** and **`excluded_asset_dirs`** — two new `zenzic.toml` fields
  covering build-time generated files and theme override directories.

### Changed

- **`find_repo_root()` root marker** — `mkdocs.yml` replaced by `.git` + `zenzic.toml`.
  Zenzic no longer requires an MkDocs configuration to locate the repository root.
- **`check_all` refactored** — `_AllCheckResults` dataclass + `_collect_all_results()`
  replace duplicated JSON/text code paths; all 6 checks (including References) are now
  covered uniformly.
- **`format` → `output_format`** parameter in `check_all`, `score`, `diff` — eliminates
  ruff A002 built-in-shadowing warning.
- **Expanded `placeholder_patterns` defaults** — 23 EN/IT stub conventions now built in.

### Fixed

- **`slug_heading()` MkDocs Material explicit anchors** — `{ #custom-id }` attribute syntax
  now correctly resolved; `{ #id }` tokens no longer treated as heading text.
- **HTML tags stripped before slugification** — inline HTML in heading text removed before
  slug computation.
- **`check_references` output** — file paths relativized to `docs_root` for CI/CD-friendly
  display.

### Tests

- **405 tests pass.** `zenzic check all` — 6/6 OK.

---

## [0.4.0-alpha.1] — 2026-03-26 — The Sovereign Architecture

---

## [0.4.0-alpha.1] — 2026-03-26 — The Sovereign Architecture

> **Breaking release candidate.** Introduces the Adapter Pipeline — a clean architectural
> boundary between the Core validator and any build engine. Migrates project documentation
> to i18n Folder Mode (`docs/it/`). Closes the RC3 cycle and opens the 0.4.0 Alpha.

### Breaking Changes

- **i18n Folder Mode migration** — Project documentation moved from Suffix Mode
  (`docs/page.it.md`) to Folder Mode (`docs/it/page.md`), matching the `mkdocs-static-i18n`
  `docs_structure: folder` convention. URL structure changes from `/page.it/` to `/it/page/`.
  Projects using Zenzic's own docs as a reference must update any hardcoded locale-suffixed paths.
- **`[build_context]` table must be declared last in `zenzic.toml`** — TOML table headers
  apply to all subsequent keys; placing `[build_context]` before other top-level fields
  silently swallowed them. Correct ordering: all top-level fields first, `[build_context]`
  at the end.

### Added

- **`BuildContext` model** — new `[build_context]` section in `zenzic.toml` declaring
  `engine`, `default_locale`, `locales`, and `fallback_to_default`. Provides Zenzic's Core
  with locale topology without parsing `mkdocs.yml` at validation time.
- **`MkDocsAdapter`** (`zenzic.core.adapter`) — build-engine adapter implementing three
  engine-agnostic methods: `is_locale_dir()`, `resolve_asset()`, `is_shadow_of_nav_page()`.
  Handles both `mkdocs` and `zensical` engines (identical folder-mode conventions).
- **`get_adapter()` factory** — single entry point; returns the appropriate adapter for the
  declared engine. Extension point for future `ZensicalAdapter` or `HugoAdapter`.
- **Automatic `mkdocs.yml` fallback** — when `build_context.locales` is empty (no
  `zenzic.toml`), both `validator.py` and `scanner.py` read locale dirs and
  `fallback_to_default` from `mkdocs.yml`. Zero-configuration projects are unaffected.
- **Nav restructure** — five semantic sections: Home / Getting Started / User Guide /
  Technical Reference / Community. Italian `nav_translations` for all 18 keys.
- **`extra.alternate`** block restored in `mkdocs.yml` — required for Zensical's Jinja2
  template to render the language selector; `reconfigure_material: true` alone is
  insufficient when the i18n plugin runs as Python (not Rust).

### Fixed

- **False-positive orphans** — all 14 `docs/it/**/*.md` files were reported as orphans
  because the old logic used a blanket locale-dir skip derived from `mkdocs.yml`. The new
  adapter checks `is_locale_dir()` via `BuildContext`, which is populated either from
  `zenzic.toml` or from the `mkdocs.yml` fallback. Zero orphan false positives.
- **False-positive broken links** — asset links in `docs/it/index.md` (e.g.
  `assets/brand/svg/zenzic-wordmark.svg`) resolved to `docs/it/assets/…` (non-existent).
  `MkDocsAdapter.resolve_asset()` now strips the locale prefix and checks the default-locale
  tree, mirroring the build engine's actual fallback behaviour.
- **`header.html` SPDX tag** — Jinja2 whitespace-stripping tags (`{#- … -#}`) caused `reuse`
  to parse `Apache-2.0 -` as an invalid SPDX expression. Replaced with `{# … #}`.
- **`overrides/` location** — moved from `docs/overrides/` to project root `overrides/`
  so that override files are not scanned as documentation pages.

### Refactored

- `validator.py` — replaced `_extract_i18n_fallback_config` / `_should_suppress_via_i18n_fallback`
  (YAML-parsing procedural logic) with `adapter.resolve_asset()`. `ConfigurationError` is
  still raised via `_extract_i18n_fallback_config` for the validation-only path.
- `scanner.py` — replaced `_extract_i18n_locale_dirs` + blanket skip with
  `adapter.is_locale_dir()`. Added `_extract_i18n_fallback_to_default()` helper.

### Tests

- All 384 tests pass. `zenzic check all` — 6/6 OK on the project's own documentation.

---

## [0.3.0-rc3] — 2026-03-25 — The Bulldozer Edition

> **Note:** Builds on `0.3.0-rc2`. Adds the Trinity of Examples (Gold Standard,
> Broken Docs, Security Lab), ISO 639-1 enforcement in suffix detection, and
> 20 chaos tests. This is the final Release Candidate before the `0.3.0` stable tag.

### Added

- **Trinity of Examples** — three reference directories in `examples/` that cover
  the full spectrum of documentation integrity:
  - `examples/i18n-standard/` — the Gold Standard: deep hierarchy, suffix mode,
    ghost artifacts (`excluded_build_artifacts`), zero absolute links, 100/100.
  - `examples/broken-docs/` — updated with absolute link violation and broken i18n
    link to demonstrate the Portability Enforcement Layer and cross-locale validation.
  - `examples/security_lab/` — updated with `traversal.md` and `absolute.md`;
    four distinct Shield and Portability triggers, all verified.
- **`examples/run_demo.sh` Philosophy Tour** — three-act orchestrator:
  Act 1 Standard (must pass), Act 2 Broken (must fail), Act 3 Shield (must block).
- **Ghost Artifact Demo** — `examples/i18n-standard/` references `assets/manual.pdf`
  and `assets/brand-kit.zip` via `excluded_build_artifacts`. Zenzic scores green
  without the files on disk — live proof of Build-Aware Intelligence.

### Changed

- **ISO 639-1 guard** — `_extract_i18n_locale_patterns` now validates locale strings
  with `re.fullmatch(r'[a-z]{2}', locale)`. Version tags (`v1`, `v2`), build
  tags (`beta`, `rc1`), numeric strings, BCP 47 region codes, and uppercase values
  are silently rejected. Only two-letter lowercase codes produce `*.locale.md`
  exclusion patterns.

### Tests

- **`tests/test_chaos_i18n.py`** — 20 chaos scenarios (ISO 639-1 guard × 11,
  orphan check pathological × 9). 367 passed, 0 failed.

---

## [0.3.0-rc2] — 2026-03-25 — The Agnostic Standard

> **Note:** Builds on `0.3.0-rc1`. Adds the Portability Enforcement Layer (absolute link
> prohibition) and migrates project documentation to engine-agnostic Suffix Mode i18n.
> Zenzic's i18n validation now works with any documentation engine without plugin dependency.

### Added

- **Absolute Link Prohibition** — Links starting with `/` now trigger a blocking error.
  Absolute paths are environment-dependent: they break when documentation is hosted in a
  subdirectory (e.g. `site.io/docs/`). Zenzic enforces relative paths (`../` or `./`) to
  make documentation portable across any hosting environment. Error message includes an
  explicit fix suggestion.
- **Agnostic Suffix-based i18n** — Support for the non-nested translation pattern
  (`page.locale.md`). Zenzic detects locale suffixes from file names independently of any
  build-engine plugin. This makes i18n validation work with Zensical, MkDocs, Hugo, or a
  bare folder of Markdown files without requiring a specific plugin to be installed.

### Fixed

- **i18n Navigation Integrity** — Migrated project documentation from Folder Mode
  (`docs/it/page.md`) to Suffix Mode (`docs/page.it.md`). Suffix Mode eliminates asset-depth
  ambiguity: translated files are siblings of originals, so all relative link paths are
  symmetric between languages. Resolves context-loss during language switching and broken
  cross-locale asset resolution (double-slash 404s generated by absolute paths in folder-mode).
- **Asset Path Symmetry** — Unified link depths for original and translated files. All
  relative paths in `.it.md` files are now identical in structure to their `.md` counterparts,
  making translation maintenance straightforward and error-free.

### Changed

- **Portability Enforcement Layer** — Pre-resolution stage added to `validate_links_async`
  that rejects absolute internal paths before the `InMemoryPathResolver` is consulted.
  Runs unconditionally regardless of engine, plugin, or locale configuration.

---

## [0.3.0-rc1] — 2026-03-25 — The Build-Aware Candidate

> **Note:** This Release Candidate supersedes the yanked 0.3.0 stable tag and incorporates
> all Sprint 4 Phase 1 and Phase 2 work. It is the baseline for the v0.3.x line.

### Added

- **Build-Aware Intelligence (i18n)** — Zenzic now understands the MkDocs `i18n` plugin in
  `folder` mode. When `fallback_to_default: true` is set in `mkdocs.yml`, links to untranslated
  pages are resolved against the default locale before being reported as broken. No false
  positives for partial translations.
- **`excluded_build_artifacts`** — new `zenzic.toml` field accepting glob patterns
  (e.g. `["pdf/*.pdf"]`) for assets generated at build time. Links to matching paths are
  suppressed at lint time without requiring the file to exist on disk.
- **Reference-style link validation** — `[text][id]` links are now resolved through the full
  `InMemoryPathResolver` pipeline (including i18n fallback). Previously invisible to the link
  checker; now first-class citizens alongside inline links.
- **`I18nFallbackConfig`** — internal `NamedTuple` encoding i18n fallback semantics
  (`enabled`, `default_locale`, `locale_dirs`). Designed for extension: any future
  locale-aware rule can consume this config without re-parsing `mkdocs.yml`.
- **Tower of Babel test suite** (`tests/test_tower_of_babel.py`) — 20 scenarios covering the
  full i18n folder-mode matrix: fully-translated pages, partial translations, ghost links,
  cross-locale direct links, case-sensitivity collisions, nested paths, orphan exclusion,
  `ConfigurationError` guards, and reference-style links across locales.
- **Engine-Agnostic Core** — Zenzic is a pure standalone CLI, usable with any documentation
  framework (MkDocs, Zensical, or none). Zero plugin dependency.
- **`InMemoryPathResolver`** — deterministic, engine-agnostic link resolver in `zenzic.core`.
  Resolves internal Markdown links against a pre-built in-memory file map. Zero I/O after
  construction; supports relative, site-absolute, and fragment links.
- **Zenzic Shield** — built-in protection against path traversal attacks during file scanning.
  `PathTraversal` surfaces as a distinct, high-severity outcome, not a generic "not found".
- **Hierarchical Configuration** — new `fail_under` field in `zenzic.toml` (0–100) with
  precedence: `--fail-under` CLI flag > `zenzic.toml` > default `0` (observational mode).
- **Dynamic Scoring v2** — `zenzic score --save` persists a `ScoreReport` JSON snapshot
  (`.zenzic-score.json`) with `score`, `threshold`, `status`, and per-category breakdown,
  ready for shields.io badge automation via `dynamic-badges-action`.
- **Bilingual documentation** — complete, synchronised EN/IT documentation across all sections.

### Fixed

- **Orphan false positives** — `find_orphans()` no longer flags files inside locale
  subdirectories (e.g. `docs/it/`) as orphaned when the i18n plugin is configured in
  `folder` mode.
- **Non-deterministic asset validation** — `validate_links_async()` previously called
  `Path.exists()` per link in the hot path, producing I/O-dependent results in CI.
  Pass 1 now builds a `known_assets: frozenset[str]` pre-map; Pass 2 uses O(1) set
  membership with zero disk I/O.
- **Null-safe YAML iteration** — `languages: null` in `mkdocs.yml` is now handled
  correctly by all i18n helpers (`or []` guard pattern). Previously raised `TypeError`
  when the key was present with a null value.
- **Entry Point** — `pyproject.toml` corrected to `zenzic.main:cli_main`, which initialises
  logging before handing off to Typer. Fixes missing log output on first invocation.
- **Type Safety** — resolved `TypeError` (`MagicMock > int`) in scorer tests caused by untyped
  config mock; `mock_load.return_value = MagicMock(fail_under=0)` now explicit in all affected tests.
- **Asset Integrity** — build artifact generation (`.zip`) automated in `run_demo.sh`,
  `nox -s preflight`, and CI, ensuring a consistent 100/100 score across all entry points.
- **`BUILD_DATE` type coercion** — format changed from `%Y-%m-%d` to `%Y/%m/%d` to prevent
  PyYAML from auto-converting the date string to `datetime.date`.
- **CVE-2026-4539 (Pygments ReDoS)** — documented accepted risk: `AdlLexer` ReDoS in Pygments
  is non-reachable in Zenzic's threat model (Zenzic does not process ADL input; Pygments is
  used only for static documentation syntax highlighting). Exemption added to `nox -s security`
  pending an upstream patch release. All other vulnerabilities remain fully audited.

### Changed

- **CLI Interface** — removed all residual MkDocs plugin references; the public API is the
  command-line interface only. Generator selection (`mkdocs.yml`) is auto-detected at runtime.
- **`zenzic.toml` self-check** — `excluded_build_artifacts = ["pdf/*.pdf"]` added to
  the repository's own configuration, removing the requirement to pre-generate PDFs
  before running `zenzic check all` locally.
- **Zenzic Shield** — Path Traversal protection now integrated into the `InMemoryPathResolver`
  core, replacing the prior ad-hoc check in the CLI wrapper.

---

## [0.3.0] — 2026-03-24 — [YANKED]

> Superseded by `0.3.0-rc1`. This tag was cut before the Build-Aware Intelligence work
> (i18n folder-mode, O(1) asset mapping, reference-style links) was merged. Use `0.3.0-rc1`.

---

## [0.2.1] — 2026-03-24

### Removed

- **`zensical.toml` support** — Zensical now reads `mkdocs.yml` natively; a
  separate `zensical.toml` is no longer required or supported as a build
  configuration file. The `examples/broken-docs/zensical.toml` fixture is
  retained only as a test asset.
- **`mkdocs` runtime dependency** — `mkdocs>=1.5.0` removed from
  `[project.dependencies]`. MkDocs plugin packages (`mkdocs-material`,
  `mkdocs-minify-plugin`, `mkdocs-with-pdf`, `mkdocstrings`, `mkdocs-static-i18n`)
  remain in `[dependency-groups.dev]` pending native Zensical equivalents for
  the social, minify, and with-pdf features.
- **MkDocs plugin entry-point** — `[project.entry-points."mkdocs.plugins"]`
  removed. Zenzic no longer registers as a `mkdocs.plugins` entry-point.
  Use `zenzic check all` in CI instead.

### Changed

- **`find_config_file()`** — looks for `mkdocs.yml` only; `zensical.toml`
  preference logic removed.
- **`find_repo_root()`** — walks up to `mkdocs.yml` or `.git`; no longer
  checks for `zensical.toml`.
- **`find_orphans()`** — TOML-branch removed; always reads `mkdocs.yml` via
  `_PermissiveYamlLoader`. i18n locale-pattern fallback branch removed.
- **`_detect_engine()`** — simplified: `mkdocs.yml` is the single config
  trigger; `zensical` is tried first (reads `mkdocs.yml` natively), then
  `mkdocs`. The `zensical.toml`-first heuristic is gone.
- **`noxfile.py`** — `docs` and `docs_serve` sessions use `zensical
  build/serve`; `preflight` uses `zensical build --strict`.
- **`justfile`** — `build`, `serve`, and `build-release` targets use
  `zensical`; `live` is now an alias for `serve`.
- **`deploy-docs.yml`** — build step uses `uv run zensical build --strict`.
- **`zenzic.yml`** — path triggers pruned to `docs/**` and `mkdocs.yml` only.
- **`mkdocs.yml`** — version bumped to `0.2.1`; comment updated to note
  native Zensical reading.
- **`pyproject.toml`** — mypy override for `mkdocs.*` removed (no longer a
  runtime dependency).

### Added

- **Documentation restructure** — new `docs/about/` section with
  `index.md`, `vision.md`, `license.md` (EN + IT); new `docs/reference/`
  section with `index.md` and `api.md` (EN + IT). The `api-reference.md`
  files remain at the flat path for backwards compatibility but are now
  also served under `reference/api.md`.
- **`mkdocs.yml` nav** — reflects the new `about/` and `reference/` layout
  with `navigation.indexes` and `navigation.expand` Material features.

---

## [0.2.0-alpha.1] — 2026-03-23

### Added

#### Two-Pass Reference Pipeline — `zenzic check references`

- **`ReferenceMap`** (`zenzic.models.references`) — per-file stateful registry for `[id]: url` reference link definitions. CommonMark §4.7 first-wins: the first definition of any ID in document order wins; subsequent definitions are ignored and tracked in `duplicate_ids`. Keys are case-insensitive (`lower().strip()`). Each entry stores `(url, line_no)` metadata for precise error reports. `integrity_score` property returns `|used_ids| / |definitions| × 100`; guarded against ZeroDivisionError — returns `100.0` when no definitions exist.
- **`ReferenceScanner`** (`zenzic.core.scanner`) — stateful per-file scanner implementing a three-phase pipeline: (1) **Harvesting** (`harvest()`) streams lines via `_iter_content_lines()` generator (O(1) RAM per line), populates `ReferenceMap`, and runs the Zenzic Shield on every URL; (2) **Cross-Check** (`cross_check()`) resolves every `[text][id]` usage against the fully-populated map, emitting `ReferenceFinding(issue="DANGLING")` for each Dangling Reference; (3) **Integrity Report** (`get_integrity_report()`) computes `integrity_score`, surfaces Dead Definitions (`issue="DEAD_DEF"`), and consolidates all findings ordered errors-first.
- **`scan_docs_references` / `scan_docs_references_with_links`** — high-level orchestrators that run the pipeline over every `.md` file in `docs/`. Shield-as-firewall contract: Pass 2 (Cross-Check) is skipped entirely for any file with `SECRET` events. Optional global URL deduplication via `LinkValidator` when `--links` is requested.
- **Zenzic Shield** (`zenzic.core.shield`) — secret-detection engine that scans every reference URL during Harvesting using pre-compiled, exact-length quantifier patterns (no backtracking, O(1) per line). Three credential families: OpenAI API key (`sk-[a-zA-Z0-9]{48}`), GitHub token (`gh[pousr]_[a-zA-Z0-9]{36}`), AWS access key (`AKIA[0-9A-Z]{16}`). Any detection causes immediate abort with **Exit Code 2**; no HTTP requests are issued for documents containing leaked credentials.
- **`LinkValidator`** (`zenzic.core.validator`) — global URL deduplication registry across the entire docs tree. `register_from_map()` registers all `http/https` URLs from a `ReferenceMap`. `validate()` issues exactly one HEAD request per unique URL regardless of how many files reference it. Reuses the existing `_check_external_links` async engine (semaphore(20), HEAD→GET fallback, 401/403/429 treated as alive).
- **`zenzic check references`** CLI command — triggers the full Three-Phase Pipeline. Flags: `--strict` (Dead Definitions become hard errors), `--links` (async HTTP validation of all reference URLs, 1 ping per unique URL). Exit Code 2 reserved exclusively for Zenzic Shield events.
- **Alt-text accessibility check** (`check_image_alt_text`) — pure function flagging both inline `![](url)` images and HTML `<img>` tags without alt text. `is_warning=True`; promoted to errors under `--strict`. Never blocks deploys by default.
- **`zenzic.models.references`** — new canonical module for `ReferenceMap`, `ReferenceFinding`, `IntegrityReport`. `zenzic.core.models` becomes a backwards-compatible re-export shim.

#### Documentation

- `docs/architecture.md` — "Two-Pass Reference Pipeline (v0.2.0)" section: stateless→document-aware comparison table, forward reference problem, lifecycle ASCII diagram, generator streaming rationale, `ReferenceMap` invariants (first-wins, case-insensitivity, line-number metadata), Shield-as-firewall design, global URL deduplication diagram, accessibility nudge, full data flow summary with LaTeX integrity formula.
- `docs/usage.md` — complete v0.2.0 rewrite: `uv`/`pip` content tabs per installation tier, `check references` with `--strict`/`--links`, Reference Integrity section with LaTeX formula, CI/CD integration section (`uvx` vs `uv run` table, GitHub Actions workflow, exit code 2 handling), Programmatic Usage section with `ReferenceScanner` API examples.
- `README.md` — reference link style throughout, `## 🛡️ Zenzic Shield` section, exit code 2 `> [!WARNING]`, updated checks table.
- All Italian locale counterparts (`*.it.md`) synchronised per Parità Documentale directive.

### Changed

- Scanning model: **stateless** (line-by-line, no memory of prior lines) → **document-aware** (Three-Phase Pipeline with per-file `ReferenceMap` state).
- Memory model: `_iter_content_lines()` generator replaces `.read()` / `.readlines()` — peak RAM scales with `ReferenceMap` size, not file size.
- Global URL deduplication extended to the reference pipeline: `LinkValidator` deduplicates at registration time across the entire docs tree — one HTTP request per unique URL regardless of reference count.

### Fixed

- **Forward Reference Trap** — single-pass scanners produce false Dangling Reference errors when `[text][id]` appears before `[id]: url` in the same file. Resolved by the Two-Pass design: Cross-Check runs only after Harvesting has fully populated the `ReferenceMap`.
- Reference ID normalisation: leading/trailing whitespace and mixed casing stripped inside `add_definition()` and `resolve()` — duplicate entries for IDs differing only in case or spacing are impossible by construction.

### Security

- **Exit Code 2** — reserved exclusively for Zenzic Shield events. If `zenzic check references` exits with code 2, a credential pattern was detected embedded in a reference URL. The pipeline aborts immediately; all HTTP requests and Cross-Check analysis are skipped. **Rotate the exposed credential immediately.**

---

## [0.1.0-alpha.1] — 2026-03-23

### 🚀 Features

#### Native link validator — no subprocesses, no MkDocs dependency

- `zenzic check links` — fully rewritten as a native two-pass Markdown validator. Pass 1 reads all `.md` files into memory and pre-computes anchor sets from ATX headings. Pass 2 extracts inline links and images via `_MARKDOWN_LINK_RE`, resolves internal paths against the in-memory file map, validates `#fragment` anchors, and rejects path traversal outside `docs/`. Pass 3 (`--strict` only) pings external URLs concurrently via `httpx` with bounded concurrency (`asyncio.Semaphore(20)`), URL deduplication, and graceful degradation for 401/403/429 responses. MkDocs is no longer required to run link validation; the check works with any MkDocs 1.x or Zensical project.

#### Quality scoring and regression detection

- `zenzic score` — aggregates all five check results into a weighted 0–100 integer. Weights: `links` 35 %, `orphans` 20 %, `snippets` 20 %, `placeholders` 15 %, `assets` 10 %. Supports `--format json`, `--save` (persists snapshot to `.zenzic-score.json`), and `--fail-under <n>` (exits non-zero if score falls below threshold).
- `zenzic diff` — compares the current score against the persisted `.zenzic-score.json` baseline; exits non-zero when the score regresses beyond `--threshold` points. Supports `--format json`.
- `zenzic check all --exit-zero` — produces the full five-check report but always exits with code 0; intended for soft-fail CI pipelines and active documentation improvement sprints.

#### Engine-agnostic development server with pre-flight shield

- `zenzic serve` — auto-detects the documentation engine (`zensical` or `mkdocs`) from the repository root and launches it with `--dev-addr 127.0.0.1:{port}`. Falls back to a static file server on `site/` when no engine binary is installed. Port resolution via socket probe before the subprocess starts (`--port`/`-p`, default `8000`, range `1024–65535`): if the requested port is busy, Zenzic probes up to ten consecutive ports and automatically selects the first free one — `Address already in use` is eliminated at the engine level. Runs a silent pre-flight check (orphans, snippets, placeholders, unused assets) before server startup; issues are surfaced as warnings without blocking. Use `--no-preflight` to skip the quality check entirely.

#### Locale-aware orphan detection

- Auto-detects `mkdocs-i18n` locale suffixes: when `mkdocs.yml` configures the `i18n` plugin with `docs_structure: suffix`, `check orphans` automatically excludes `*.{locale}.md` files for every non-default locale — zero configuration required, works for any number of languages.

#### Configuration

- `excluded_assets` field in `ZenzicConfig` — list of asset paths (relative to `docs_dir`) excluded from the unused-assets check; intended for files referenced by `mkdocs.yml` or theme templates (favicons, logos, social preview images).
- `excluded_file_patterns` field in `ZenzicConfig` — list of filename glob patterns excluded from the orphan check; escape hatch for locale schemes that cannot be auto-detected.

#### Core library

- `zenzic.core.scorer` — pure scoring engine (`compute_score`, `save_snapshot`, `load_snapshot`) decoupled from I/O; fully unit-tested.
- `zenzic.core.exceptions` — structured exception hierarchy: `ZenzicError` (base, carries optional `context: dict`), `ConfigurationError`, `EngineError`, `CheckError`, `NetworkError`.
- `zenzic.core.logging` — `get_logger(name)` and `setup_cli_logging(level)` via standard `logging` + `RichHandler`; plugin mode continues to use `logging.getLogger("mkdocs.plugins.zenzic")` without interference.

### 🛡️ Quality & Testing

- **98.4 % test coverage** across `zenzic.core.*` and CLI wrappers.
- **Async link-validation mocking** — `_check_external_links` is exercised with `pytest-asyncio` and `respx` transport mocks; no outbound HTTP connections during CI.
- **Two-phase code-block isolation in `extract_links()`** — the link regex runs only on "safe" text. Phase 1a: a line-by-line state machine skips every line inside a fenced block (```` ``` ```` / `~~~`). Phase 1b: inline code spans are replaced character-for-character with spaces via `re.sub` before the regex runs. Links inside code examples are eliminated by construction; no regex backtracking, O(n) in file lines.
- **`PermissiveYamlLoader` in `scanner.py`** — replaces `yaml.safe_load`, which was silently swallowing `!ENV` tags and leaving `doc_config = {}`, causing every page to be reported as an orphan on projects that use environment-variable interpolation in `mkdocs.yml`.

### 📦 DevOps

- **PyPI release via OIDC** — `release.yml` workflow publishes to PyPI using OpenID Connect trusted publishing; no long-lived API tokens stored in GitHub Secrets.
- **hatch build backend** — `pyproject.toml` migrated from setuptools to `hatchling`; version sourced from git tags via `hatch-vcs` for reproducible builds.
- **`zensical` as optional extra** — `zensical` dependency moved to `optional-dependencies[zensical]`; `pip install zenzic` installs no documentation-generator binaries. Install `zenzic[zensical]` only on projects that use Zensical as the build driver.
- **Multi-language documentation (EN/IT)** — all user-facing pages (`usage`, `checks`, `configuration`, `architecture`) are available in English and Italian; locale suffix auto-detection ensures the orphan check passes on all locale variants.
- **Documentation overhaul** — `docs/index.md` rewritten as a proper landing page with problem statement and "Where to go next" navigation; `docs/usage.md` expanded with scoring rationale, CI patterns, and plugin hook explanations; `docs/checks.md` enriched with problem context and example output per check; `docs/configuration.md` adds a "Getting started" section with zero-config examples; `docs/architecture.md` updated with the three-layer diagram, link extraction pipeline, two-phase isolation model, and async validation concurrency design.
- **`justfile` rationalised** — removed `lint`, `check`, and `build` tasks that duplicated `nox` sessions; `clean` no longer removes `.nox/` to preserve the cached virtualenv across runs.

### Changed

- `_detect_engine()` — `--engine` override now validates both binary presence on `$PATH` and required config file existence before returning; `--engine zensical` accepts `mkdocs.yml` as a valid config for backwards compatibility (Zensical is a superset of MkDocs); returns `None` when no config file is present, enabling the static-server fallback instead of raising an error.

### Removed

- `zenzic build` — generator build wrapper removed. It was a thin subprocess delegating entirely to `mkdocs build` / `zensical build`, adding no linting value and silently bypassing MkDocs plugins (`i18n`, `social`, `minify`, `with-pdf`) and Material theme configuration. Use your generator directly: `mkdocs build`, `zensical build`.
- `detect_generator()` and `DocEngine` from `zenzic.models.config` — replaced by `find_config_file()` in `zenzic.core.scanner`, which returns the nav config path without generator-name or binary-availability metadata.

### ⚠️ Known Limitations

- **Inline links and images only.** `_MARKDOWN_LINK_RE` captures `[text](url)` and `![alt](url)` forms. Reference-style links (`[text][id]`) require a multi-pass, stateful parser (a per-file reference map) and are planned for v0.2.0.
- `check snippets`, `check placeholders`, and `check assets` scan locale-suffixed files (e.g., `index.it.md`) produced by `mkdocs-i18n`. This is intentional for snippet and placeholder validation but may produce duplicate asset-reference findings. Per-check exclusion via `excluded_file_patterns` scope is planned.

---

## [0.1.0] — 2026-03-18

### Added

- `zenzic check links` — strict broken-link and anchor detection via `mkdocs build --strict`
- `zenzic check orphans` — detect `.md` files missing from `nav`
- `zenzic check snippets` — syntax-check all fenced Python code blocks
- `zenzic check placeholders` — flag stub pages and forbidden placeholder text
- `zenzic check assets` — detect unused images and assets
- `zenzic check all` — run all checks in a single command; supports `--format json` for CI/CD integration
- Professional PDF generation — integrated `with-pdf` plugin with custom Jinja2 brand cover, PythonWoods gradient, and dynamic build timestamp
- `zenzic.toml` configuration file with Pydantic v2 models; all fields optional with sane defaults
- `justfile` — integrated task runner for rapid development (sync, lint, dev, build-release)
- `examples/broken-docs/` — intentionally broken documentation repo covering all five check types
- `noxfile.py` — developer task runner: `tests`, `lint`, `format`, `typecheck`, `reuse`, `security`, `docs`, `preflight`, `screenshot`, `bump`
- `scripts/generate_screenshot.py` — reproducible SVG terminal screenshot via Rich `Console(record=True)`
- Full REUSE 3.3 / SPDX compliance across all source files
- GitHub Actions — `ci.yml`, `release.yml`, `sbom.yml`, `secret-scan.yml`, `security-posture.yml`, `dependabot.yml`
- Documentation suite — index, architecture (using absolute `zenzic.core` paths), checks reference, and configuration reference
- Pre-commit hooks — ruff, mypy, reuse, zenzic self-check

<!-- ─── Reference link definitions ──────────────────────────────────────────── -->

[Unreleased]:       https://github.com/PythonWoods/zenzic/compare/v0.3.0...HEAD
[0.3.0]:            https://github.com/PythonWoods/zenzic/compare/v0.2.1...v0.3.0
[0.3.0-rc1]:        https://github.com/PythonWoods/zenzic/compare/v0.2.1...v0.3.0-rc1
[0.2.1]:            https://github.com/PythonWoods/zenzic/compare/v0.2.0-alpha.1...v0.2.1
[0.2.0-alpha.1]:    https://github.com/PythonWoods/zenzic/compare/v0.1.0-alpha.1...v0.2.0-alpha.1
[0.1.0-alpha.1]:    https://github.com/PythonWoods/zenzic/compare/v0.1.0...v0.1.0-alpha.1
[0.1.0]:            https://github.com/PythonWoods/zenzic/releases/tag/v0.1.0
