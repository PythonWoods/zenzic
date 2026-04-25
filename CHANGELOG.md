<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

> **Older versions (v0.1.0 – v0.5.x):** See the [Changelog Archive](CHANGELOG.archive.md).

## [Unreleased]

## [0.7.0] — 2026-04-22 — Obsidian Maturity (Stable)

> ⚓ Zenzic v0.7.0 marks the consolidation of our core architecture and the full alignment with official specifications. Supersedes v0.6.1.
>
> **Legacy Documentation:** Versions prior to v0.7.0 are officially deprecated and do not follow
> the current Diátaxis architecture. For historical reference, see the
> [v0.6.1 GitHub Release](https://github.com/PythonWoods/zenzic/releases/tag/v0.6.1).
> The v0.7.0 documentation at [zenzic.dev](https://zenzic.dev) is the authoritative source.

### ⚠️ BREAKING CHANGE — MkDocs Plugin Removed (Direttiva CEO 055)

> **DEPRECATION & REMOVAL:** The internal MkDocs plugin (`zenzic.integrations.mkdocs`) has been
> permanently removed. Zenzic is now a **Sovereign CLI**. This ensures that every user, regardless
> of their engine, benefits from the full power of the Virtual Site Map (VSM), the Shield
> (credential scanning with ZRT-006/007 hardening), and the Blood Sentinel (path-traversal
> detection). Internal engine integrations are officially replaced by the engine-agnostic CLI
> workflow.

**Migration:** Remove `pip install "zenzic[mkdocs]"` and the `plugins: - zenzic` entry from
`mkdocs.yml`. Add `zenzic check all` as a CI step (before or after `mkdocs build`):

```yaml
# GitHub Actions — replace the MkDocs plugin gate with:
- run: zenzic check all --strict
```

The `[mkdocs]` optional extra no longer exists. `pip install zenzic` is the complete install.

---

### Architectural Refactoring — Sovereign CLI & Core Law Enforcement (Direttive 061–068)

#### ⚠️ BREAKING CHANGE — `zenzic plugins` Command Removed (Direttiva CEO 068)

> **REMOVED:** The `zenzic plugins` command has been entirely removed in v0.7.0.
> `zenzic inspect` is now the **only** introspection interface. If you invoke
> `zenzic plugins`, the CLI responds with `No such command 'plugins'`.
>
> **Migration:** Replace any script or CI step that calls `zenzic plugins list`
> with `zenzic inspect capabilities`.

#### Changed

- **`zenzic plugins` rebranded to `zenzic inspect`; sub-command `list` → `capabilities` then removed (Direttive 061-B, 068 — "The Sovereign Rebranding" / "The Total Decapitation of 'Plugins'").**
  The introspection command is now exclusively `zenzic inspect capabilities`.
  `inspect` is the canonical name; `plugins` is gone from the CLI entirely.

- **`src/zenzic/ui.py` relocated to `src/zenzic/core/ui.py` (Direttiva 062-B — "The Core Law Enforcement").**
  `SentinelReporter` (in `core/`) imported `zenzic.ui`, violating the layer law that the core must
  never look upward. `ObsidianPalette`, `ObsidianUI`, `make_banner`, `emoji`, and `SUPPORTS_COLOR`
  now live canonically in `zenzic.core.ui`. The old path `zenzic.ui` is kept as a one-line
  compatibility stub (`from zenzic.core.ui import *`) so third-party code is unaffected.

- **`src/zenzic/lab.py` relocated to `src/zenzic/cli/_lab.py` (Direttiva 063 — "The Final Relocation").**
  The Lab command is CLI orchestration, not core logic. Moving it into the `cli/` package aligns
  it with `_check.py`, `_clean.py`, and `_inspect.py` — all commands live in the same layer.

- **`run_rule()` moved from `src/zenzic/rules.py` to `src/zenzic/core/rules.py` (Direttiva 064 — "The SDK Cleansing" / "Bonifica dell'SDK").**
  The test helper that runs a single plugin rule against a Markdown string is now part of the core
  engine. `src/zenzic/rules.py` is reduced to a six-line SDK façade re-exporting
  `BaseRule`, `CustomRule`, `RuleFinding`, `Severity`, `Violation`, and `run_rule` from `core`.
  All existing `from zenzic.rules import ...` statements remain valid with zero changes.

#### Removed

- **`src/zenzic/integrations/` directory physically purged (Direttiva 066 — "The Physical Purge").**
  The `zenzic.integrations.mkdocs` plugin had already been deprecated by Direttiva 055 (Breaking
  Change above). The directory is now deleted from the repository — no ghost files remain.
  Zenzic is a pure **Sovereign CLI**; there are no embedded engine hooks.

---

### Docusaurus Protocol Support (Direttiva CEO 117)

#### Added

- **`pathname:///` URL scheme — Docusaurus Compatibility (Direttiva CEO 117).**
  Zenzic now natively recognises the `pathname:///` URL scheme used in Docusaurus to
  reference static assets (PDFs, standalone HTML pages, downloads) that live outside
  the React router and are served directly by the dev server / CDN.
  - **Engine-aware:** the bypass is active **only** when `engine = "docusaurus"`.
    Projects using `mkdocs`, `zensical`, or `standalone` will still receive a
    `Z105 ABSOLUTE_PATH` error for any `pathname:///` link, guiding migration.
  - **Implementation:** `_DOCUSAURUS_SKIP_SCHEMES` constant added to `validator.py`;
    the validation loop resolves the effective skip tuple per-run from `config.build_context.engine`.
    `pathname:` removed from the global `_SKIP_SCHEMES` to preserve engine isolation.
  - **Tested:** `TestPathnameProtocolSupport` in `test_docusaurus_adapter.py` covers
    constant isolation, Docusaurus no-error, and MkDocs Z105 assertion.
  - **Documented:** `docs/reference/engines.mdx` and IT mirror gain
    "Special URL schemes" section under the Docusaurus chapter.

---

### The Agnostic Universalism: Z404 for All Engines (Direttiva CEO 087)

#### Added

- **Z404 extended to MkDocs and Zensical (Direttiva 087).** `check_config_assets()`
  implemented in `_mkdocs.py` (checks `theme.favicon` + `theme.logo` against `docs_dir/`)
  and `_zensical.py` (checks `[project].favicon` + `[project].logo` against `[project].docs_dir/`).
  Icon names (e.g. `material/library`) are skipped via image-extension filter.
  `cli.py` Z404 block replaced with a multi-engine dispatch (`docusaurus` / `mkdocs` / `zensical`).
- **Lab Acts 9 & 10: MkDocs Favicon Guard + Zensical Logo Guard (Direttiva 087).**
  Two new Lab acts and corresponding example fixtures (`examples/mkdocs-z404/`,
  `examples/zensical-z404/`) demonstrate Z404 detection across all three supported
  engines. The act validator updated to `0–10`.

#### Changed

- **Z404 documentation rewritten as engine-agnostic (Direttiva 087).** `finding-codes.mdx`
  (EN + IT) Z404 section now covers all three engines—Docusaurus, MkDocs, Zensical—with
  per-engine field tables, per-engine remediation snippets, and an updated Adapter
  Coverage note confirming universal support.

---

### The Obsidian Mirror Pass: Lab, Shield & Docs Alignment (Direttive 082–086)

#### Added

- **Z404 CONFIG_ASSET_MISSING (Direttiva 085).** The Docusaurus adapter now statically
  analyses `docusaurus.config.ts` and verifies that every `favicon:` and `image:`
  (OG social card) path resolves to a real file inside `static/`. Implemented as
  `check_config_assets()` in `_docusaurus.py` — pure regex, zero subprocess. Code
  registered in `codes.py`; wired via `_AllCheckResults.config_asset_issues` in
  `cli.py`. Severity: `warning` (promote to Exit 1 via `--strict`).
- **Lab Obsidian Seal (Direttiva 086).** Every `zenzic lab <N>` run now closes with
  a dedicated **Obsidian Seal** panel (indigo border, Sentinel Palette colours) showing
  file count, elapsed time, throughput in files/s, and a per-act pass/fail verdict.
  Full-run summaries (`zenzic lab` with all acts) render an aggregate Obsidian Seal
  with total throughput across acts.
- **Lab throughput fields (Direttiva 086).** `_ActResult` gains `docs_count`,
  `assets_count`, `total_files`, and `throughput` properties. The full-run summary
  table now shows a **Files** column and a **files/s** column alongside the existing
  engine and result columns.
- **Dependabot GitHub Actions coverage (Direttiva 085).** `zenzic-doc/.github/dependabot.yml`
  previously only covered npm. Extended with a `github-actions` ecosystem entry and
  two dependency groups (`docusaurus-all`, `react-ecosystem`) to reduce PR noise.
- **zenzic-doc `scripts/bump-version.sh` + `just bump` recipe (Direttiva 083).**
  Automated version bump script covering all six hardcoded version strings in the doc
  portal: `docusaurus.config.ts`, `Quickstart.tsx`, `Hero.tsx`, `src/pages/index.tsx`
  (LD+JSON `softwareVersion`), `i18n/en/code.json`, `i18n/it/code.json`.
- **zenzic-doc GitHub Release workflow (Direttiva 082).** `.github/workflows/release.yml`
  added — triggers on `v*.*.*` tags, builds the Docusaurus site, creates a GitHub
  Release with the build artefact attached.

#### Changed

- **Lab UI rebuilt with Sentinel Palette (Direttiva 086).** `_print_summary` now uses
  `INDIGO` header style, `SLATE` dim columns, and the branded `⬡ ZENZIC LAB — Full Run
  Summary` title replacing the plain `Lab Summary` heading.
- **Lab act title panels now use Indigo border (Direttiva 082).** Per-act header Panel
  uses `border_style="#4f46e5"` to match the Sentinel Palette — identical to the live
  `SentinelReporter` output.
- **Z404 documented across all surfaces (Direttiva 086).** `finding-codes.mdx` (EN + IT)
  now contains a full `Config Asset Integrity` section with technical explanation, field
  table, severity rationale, remediation steps, and adapter-coverage note.
  `README.md` and `README.it.md` Capability Matrix both include a `Config asset
  integrity` row referencing `Z404`.
- **zenzic-doc dependencies bumped (Direttiva 086).** `package.json` updated:
  `tailwindcss` 4.2.2 → 4.2.4 · `@tailwindcss/postcss` 4.2.2 → 4.2.4 ·
  `autoprefixer` 10.4.27 → 10.5.0 · `postcss` 8.5.9 → 8.5.10 ·
  `typescript` 6.0.2 → 6.0.3. Production build confirmed green.

#### Fixed

- **zenzic-doc favicon 404 (Direttiva 084).** `docusaurus.config.ts` declared
  `favicon: 'img/favicon.ico'` — a path that did not exist in `static/`. Corrected
  to `'assets/favicon/png/zenzic-icon-32.png'` (the real file). This was the exact
  class of infrastructure fault that Z404 was built to catch.
- **OG/Twitter meta tag completeness (Direttiva 084).** Three meta tags were absent:
  `twitter:image:alt`, `og:image:width` (1200), `og:image:height` (630). Added to
  `docusaurus.config.ts`. Social card asset confirmed at 1200×630 px, 33 KB.
- **GitHub release v0.6.1 marked as superseded (Direttiva 085).** Both the core repo
  and the `zenzic-doc` repo v0.6.1 GitHub Release titles updated to
  `[SUPERSEDED by v0.6.2]` with a `[!WARNING]` callout prepended to the release notes.

---

### Obsidian Maturity Pass: UX Hardening & Truth Audit (Direttive 076–079)

#### Added

- **Z104 Proactive Suggestion Engine (Direttiva 077).** When a link target is not found
  (`Z104 FILE_NOT_FOUND`), Zenzic now computes the closest file in the VSM using
  `difflib.get_close_matches` (cutoff 0.6) and appends a `💡 Did you mean: '...'?`
  hint to the error message. No disk I/O in the hot path — diff runs against the
  in-memory `md_contents` map built in Pass 1.
- **README Perimeter Invariant (Direttiva CEO 076).** `zenzic.toml` for the core
  repository now carries an explicit `⚠ PERIMETER INVARIANT` comment documenting
  that `docs_dir = "."` is a safety invariant that keeps `README.md` and
  `README.it.md` inside the validation perimeter. Changing `docs_dir` without
  re-adding these files would create a false-safety gap.

#### Changed

- **Standalone Truth Audit (Direttiva 078).** Every user-facing description of
  Standalone Mode now explicitly declares that orphan detection (`Z402`) is
  disabled because there is no navigation contract. Replaced "structural integrity"
  with "file integrity" to reflect the actual capability. `README.md`, `README.it.md`,
  and all example files updated.
- **Engineering Ledger replaces Design Philosophy.** The `## Design Philosophy`
  section in `README.md` and `README.it.md` has been rebuilt as an HTML-table
  Engineering Ledger (three non-negotiable contracts: Zero Assumptions, Subprocess-Free,
  Deterministic Compliance) with real code fragments as evidence.
- **Vanilla Purge — examples.** All example `zenzic.toml` files previously using
  `engine = "vanilla"` now use `engine = "standalone"`. Affected:
  `examples/vanilla/`, `examples/standalone-markdown/`, `examples/custom-dir-target/`,
  `examples/single-file-target/`. Inline Markdown content and README files
  inside these examples have been rewritten accordingly.
- **Version references.** `pyproject.toml`, `src/zenzic/__init__.py`, and
  `CITATION.cff` bumped from `0.6.1` to `0.6.2`. Release date: 2026-04-22.

#### Fixed

- **Sentinel Mesh Tightening — Stale Diátaxis Links (Direttiva 079).** Forensic audit
  revealed that `README.md` contained three link targets that became stale after the
  Diátaxis documentation restructure:
  - `https://zenzic.dev/docs/usage/badges/` → `https://zenzic.dev/docs/how-to/add-badges/`
  - `https://zenzic.dev/docs/guides/ci-cd/` → `https://zenzic.dev/docs/how-to/configure-ci-cd/`
  - `https://zenzic.dev/docs/internals/architecture-overview/` → `https://zenzic.dev/docs/explanation/architecture/`
  Same three corrected in `README.it.md` (`/it/docs/` prefix).
- **Blanket zenzic.dev Exclusion Removed (Direttiva 079).** The `excluded_external_urls`
  entry `"https://zenzic.dev/"` was a temporary workaround added when the documentation
  site was not yet deployed. It became a permanent blindspot, silencing `--strict`
  validation of all portal links even as they rotted. The entry has been removed.
  A runtime flag (`--exclude-url https://zenzic.dev/`) is the correct escape hatch for
  offline CI runners rather than a config-file bypass.
- **zenzic-doc Developer README.** Node.js prerequisite corrected from 20 to 24.
  CI matrix wording updated to "Node 22 and 24". Stale i18n route `/docs/intro`
  replaced with the correct `/docs/` (root index) following the Diátaxis restructure.

---

### Guardians Security Audit & Final Hardening Sprint (Direttive 050–052)

#### Added

- **`gitlab-pat` — 9th Shield pattern family.** `glpat-[A-Za-z0-9\-_]{20,}` added
  to the Shield pattern registry in `src/zenzic/core/shield.py`. The README capability
  matrix already reflected 9 families; the missing pattern has been registered and
  documented. `README.md` and `README.it.md` Shield prose updated from "GitHub/GitLab"
  to "GitHub, GitLab PAT" to reflect the distinct family.
- **CLI de-monolitization — `cli.py` → `cli/` package.** `src/zenzic/cli.py` (1 968
  lines, 4 responsibility domains) has been split into a coherent package:

  | Module | Responsibility |
  |:-------|:---------------|
  | `_shared.py` | `console` / `_ui` singletons, `configure_console()`, cross-command utilities |
  | `_check.py` | `check_app` + seven `check *` commands |
  | `_clean.py` | `clean_app` + `clean assets` command |
  | `_plugins.py` | `plugins_app` + `plugins list` command |
  | `_standalone.py` | `score`, `diff`, `init` commands |
  | `__init__.py` | Public re-export surface — `main.py` import contract unchanged |

  The **Visual State Guardian** law is enforced: no command module may instantiate
  `Console()` or `ObsidianUI()` directly. All output routes through `get_ui()` and
  `get_console()` from `_shared.py`.

#### Changed

- **Shield Hardening — ZRT-006 documented.** `_normalize_line_for_shield()` already
  stripped Unicode format characters (category Cf — zero-width joiners, soft hyphens,
  etc.) and decoded HTML character references (`html.unescape()`). These capabilities
  were present in code since v0.6.1 but absent from documentation. Added to
  `architecture.mdx` (EN + IT) Pre-scan Normalizer table.
- **Shield Hardening — ZRT-007 documented.** Comment interleaving stripping
  (`_HTML_COMMENT_RE`, `_MDX_COMMENT_RE`) and the 1-line lookback buffer
  (`scan_lines_with_lookback()`) were live in `shield.py` but undocumented.
  `scan_lines_with_lookback()` joins `prev_normalized[-80:] + current_normalized[:80]`
  and scans the concatenation to catch secrets split across YAML folded scalars or
  Markdown line breaks. Added to `architecture.mdx` Hardening section (EN + IT).
- **Tripla Parità: Codice = Docs EN = Docs IT (Direttiva 051).** Forensic audit
  eliminated a 125-line content delta between EN and IT `architecture.mdx` caused by
  missing technical content (not natural-language verbosity). Eight targeted additions
  brought the delta to +36 lines — genuinely fisiologico for bilingual prose.
  Pre-scan Normalizer table expanded from 3 rows (ZRT-003 only) to 6 rows (ZRT-006,
  ZRT-007, ZRT-003). Pattern Families table updated from 8 to 9 rows. Hardening
  section gains the lookback buffer bullet. All changes mirrored to IT.

---

### Enterprise CI Expansion (Direttive CEO 092–095)

#### Added

- **SARIF 2.1.0 Export — `--format sarif` (Direttiva CEO 092).**
  All `check` sub-commands (`links`, `orphans`, `snippets`, `references`, `assets`, `all`)
  now accept `--format sarif`. The formatter produces valid SARIF 2.1.0 JSON with the
  SchemaStore `$schema` URL (`https://json.schemastore.org/sarif-2.1.0.json`), named
  rule entries, and `properties.security-severity` scores (`9.5` for `security_breach`,
  `9.0` for `security_incident`). Uploading `zenzic-results.sarif` to GitHub Code
  Scanning surfaces findings inline in Pull Request diffs and the repository Security tab
  — no log parsing required.
- **Cross-Platform CI Matrix — Windows & macOS runners (Direttiva CEO 093).**
  The `quality` job in `.github/workflows/ci.yml` now tests every commit across a
  `3 × 3` matrix: `os: [ubuntu-latest, windows-latest, macos-latest]` ×
  `python-version: ["3.11", "3.12", "3.13"]`. `fail-fast: false` ensures all 9
  combinations are reported. Coverage upload is scoped to `ubuntu-latest / 3.13`.
- **Official GitHub Action — `PythonWoods/zenzic-action` (Direttiva CEO 094).**
  Composite action scaffolded in the `zenzic-action` repository. Installs Zenzic via
  `uv tool install`, runs `check all --format sarif`, writes `zenzic-results.sarif`,
  and uploads via `github/codeql-action/upload-sarif`. Configurable inputs: `version`,
  `docs-dir`, `format`, `sarif-file`, `upload-sarif`, `strict`, `fail-on-error`.
  Removes the need for manual `uvx zenzic` invocations in CI.

---

### Bilingual Integrity Seal — Multi-Root Safe Harbor Sprint (D123–D128)

#### Added

- **Multi-Root Path Resolution** (D124) — `InMemoryPathResolver` now accepts
  `allowed_roots: list[Path]`. When locale roots are provided, cross-locale
  relative links (e.g. `i18n/it/intro.md` → `i18n/it/guide.md`) resolve
  correctly instead of triggering a false-positive `PATH_TRAVERSAL_SUSPICIOUS`.
  Security invariant is preserved: targets outside all authorised roots are
  still rejected.

- **Mandatory i18n Anchor Integrity** (D125) — Same-page anchor validation is
  now **always active** for files inside `i18n/` locale directories, regardless
  of the `validate_same_page_anchors` config flag. A translator updating
  `[link](#contesto)` while leaving the heading as `{#context}` is caught
  immediately.

- **Expanded `@site/` Alias to `repo_root`** (D123) — `known_assets` now scans
  `repo_root` rather than only `docs_root`, so Docusaurus `@site/static/` image
  references inside locale files resolve correctly.

- **Docusaurus auto-detection in `zenzic init`** (D128) — `zenzic init` now
  detects `docusaurus.config.ts` / `docusaurus.config.js` and emits an expanded
  `[build_context]` template with i18n commentary and the Multi-Root Safe Harbor
  note. Configuration reference URL updated to `zenzic.dev/docs/reference/`.

---

### Codebase Parity & Platform Robustness Sprint (2026-04-24)

#### Fixed

- **Case-sensitive asset fallback on Windows / macOS** — `resolve_asset()` in all
  three adapter modules (`_mkdocs.py`, `_zensical.py`, `_docusaurus.py`) used
  `Path.exists()` to test fallback paths, which returns `True` on case-insensitive
  filesystems regardless of capitalisation. Replaced with `case_sensitive_exists()`
  (new helper in `_utils.py`, using `os.listdir()`) which enforces exact case
  matching on every platform. Fixes a CI regression surfaced on the Windows and macOS
  legs of the cross-platform matrix.

- **MDX / HTML comments excluded from placeholder word count** —
  `check_placeholder_content()` counted words in raw Markdown source, causing
  `{/* … */}` MDX block-comments and `<!-- … -->` HTML comments to inflate the
  visible word count. A file below the `placeholder_max_words` threshold was not
  flagged if it contained a long comment header. Introduced `_visible_word_count(text)`
  which strips YAML frontmatter, MDX comments, and HTML comments before splitting.
  Regression test `test_placeholder_mdx_comments_excluded_from_word_count` added.

- **Z000 migration guard promoted from TODO to permanent** — `_factory.py` carried
  `# TODO: Remove this migration guard in v0.7.0`, implying the `engine = "vanilla"`
  check was temporary. The guard is intentionally permanent (vanilla was removed in
  v0.6.1); replaced with an explanatory comment.

- **Documentation parity audit** (zenzic-doc) — Thirteen remaining references to the
  removed `VanillaAdapter` class replaced with `StandaloneAdapter` (EN + IT locales).
  JSON examples in `cli.mdx` and `configure-ci-cd.mdx` used the non-existent code
  `"BROKEN_LINK"`; corrected to `"Z104"` with canonical message format. Z000 entry in
  `finding-codes.mdx` now explicitly documents it as a `ConfigurationError` exception
  absent from `--format json` output. Reference scanner ASCII diagram in `checks.mdx`
  replaced with a Mermaid `flowchart LR` using ObsidianPalette colours.

#### Security

- **CVE-2026-3219 — pip polyglot archive handling** — `pip 26.0.1` is affected by
  CVE-2026-3219 (concatenated tar + ZIP archives treated as ZIP regardless of filename;
  no patched release on PyPI). Zenzic uses `uv` for all package management and never
  invokes pip programmatically; pip is a transitive dev-only dependency of pip-audit.
  All packages are pinned in `uv.lock`. Added `--ignore-vuln CVE-2026-3219` to the
  `nox security` session with a removal reminder.

---

### Test Coverage & Mutation Testing Sprint (2026-04-24)

#### Added

- **`tests/test_cache.py`** (29 tests) — full coverage of `src/zenzic/core/cache.py`.
  Pure hash helpers (`make_content_hash`, `make_config_hash`, `make_vsm_snapshot_hash`,
  `make_file_key`) and `CacheManager` in-memory and I/O operations (`get`, `put`, `load`,
  `save`). Covers atomic write, parent-dir creation, corrupt-JSON fallback, and OSError
  cleanup via `json.dump` monkeypatching.

- **`tests/test_reporter.py`** (12 tests) — coverage of `_read_snippet` and `_strip_prefix`
  in `src/zenzic/core/reporter.py`. Exercises `or`/`and` boundary in the empty-file /
  invalid-line-no guard, context-window clamping at file start and end, and prefix
  stripping semantics (line 0 bypass, partial-match retention).

- **`TestToCanonicalUrlMutantKill`** (15 tests) added to `tests/test_rules.py` — targets
  `VSMBrokenLinkRule._to_canonical_url`. Kills `rstrip(None)` / `lstrip("/")` mutations,
  backslash normalisation, `index.md` → parent-dir strip, context-aware `..` resolution,
  `source_dir`/`docs_root` guard logic inversions, and `"."` relative-path edge case.

- **`TestObfuscateSecretMutantKill`** (7 tests) added to `tests/test_redteam_remediation.py`
  — targets `_obfuscate_secret` in `reporter.py`. Kills `<= 8` → `< 8`, `<= 8` → `<= 9`
  boundary mutations and `raw[:4]` → `raw[:5]` prefix-width mutation. Verifies star count
  equals `len(raw) - 8` and total length is always preserved.

- **`TestNormalizeLineForShieldMutantKill`** (4 tests) added to
  `tests/test_shield_obfuscation.py` — kills MDX-comment sub → `"XXXX"` (mutmut_22),
  table-pipe sub → `"XX XX"` (mutmut_40), and whitespace join → `"XX XX".join` (mutmut_42).

- **`mutmut` mutation testing run** on `rules.py`, `shield.py`, `reporter.py` — full run
  completed. 200+ surviving mutants analysed; high-impact logic mutants in
  `_to_canonical_url`, `_obfuscate_secret`, and `_normalize_line_for_shield` killed by new
  tests. Remaining surviving mutants classified as equivalent (template string variations in
  `SentinelReporter.render`, defensive assertions, or `encoding="UTF-8"` / `errors="REPLACE"`
  mutations with identical runtime behaviour).

---

### Sentinel Integrity & Knowledge Codification Sprint (D041–D047 — 2026-04-25)

#### Fixed

- **Blood Sentinel false positive — explicit external targets (Direttiva CEO 043 — "The Sentinel's Sanity Pass").**
  `zenzic check all ../external-path` raised Exit 3 (Blood Sentinel) when the explicit target
  lived outside the CWD repository root. `_validate_docs_root` (F4-1 guard) treated any
  `docs_root` outside `repo_root` as a path traversal attack, regardless of whether the user
  had explicitly provided that path as a CLI argument.
  **Fix (ADR-007 — Sovereign Sandbox):** After resolving `docs_root`, if
  `docs_root.relative_to(repo_root)` raises `ValueError`, reassign `repo_root = docs_root`.
  The explicit user target becomes the sovereign sandbox; Blood Sentinel then guards escapes
  _from_ that target, not the _location_ of it.
  Integration test `test_check_all_external_docs_root_not_blocked_by_sentinel` added to
  `tests/test_cli.py`.

- **Zenzic banner missing on early fatal exits (Direttiva CEO 043).**
  `_ui.print_header(__version__)` was called inside the text-format display block, after all
  validation. Any fatal exit before that point (missing config, Blood Sentinel rejection, Shield
  breach) produced output with no banner. **Fix:** banner hoisted to the start of `check_all`,
  guarded by `not quiet and output_format == "text"`.

#### Documentation

- **Frontmatter integrity confirmed — ZRT-001 audit (Direttiva CEO 041).**
  Confirmed that `check_shield()` scans via `enumerate(fh, start=1)` — every line including
  YAML frontmatter — before any filtered pass. The `_visible_word_count()` fix (Codebase Parity
  Sprint) strips frontmatter for Z502 word-count only and has zero impact on Shield coverage.
  No code change required.

- **Agent Instruction Obsidian Ledger (Direttive CEO 046–047 — "The Knowledge Refactoring" / "The Knowledge Trinity").**
  All three repository `.github/copilot-instructions.md` files rewritten into the Obsidian Ledger
  schema: `[MANIFESTO] → [POLICIES] → [ARCHITECTURE] → [ADR] → [CHRONICLES] → [SPRINT LOG]`.
  Architectural corrections applied: `cli/` package structure, `core/ui.py`, `cli/_lab.py`,
  11 Acts (0–10), Z504 `QUALITY_REGRESSION` documented for the first time. `zenzic-action`
  receives its first-ever agent instruction file (`.github/` directory created from scratch).

- **Memory Law codified (Direttiva CEO 042).**
  Section 9 — "Documenting Evolution (The Memory Law)" — added to both `zenzic` and `zenzic-doc`
  agent instruction files. Agents must codify all sprint innovations before a directive is closed.

- **Bilingual Structural Invariant codified (Direttiva CEO 045 — "Codifying the Symmetry").**
  Law of Italian Mirroring formally codified in both agent instruction files: any `git mv` in
  `docs/` must be accompanied by a corresponding `git mv` in `i18n/it/` **in the same commit**.
  Symmetry audit (diff command) run and confirmed zero asymmetries.

---

### Obsidian Memory Law & Precision Polish Sprint (D048–D049 — 2026-04-25)

#### Fixed

- **Z502 `SHORT_CONTENT` pointer targeting frontmatter (Direttiva CEO 048 — Bug 1).**
  `check_placeholder_content` had `line_no=1` hardcoded in the short-content `PlaceholderFinding`,
  causing the diagnostic `❱` arrow to point at the opening `---` of YAML frontmatter — not the
  first content line. **Fix:** `_first_content_line(text)` uses `_FRONTMATTER_RE.match()` to
  count newlines through the frontmatter block and return the first post-frontmatter line number.
  Test: `test_short_content_pointer_skips_frontmatter`.

- **Z503 YAML snippet errors report relative line instead of absolute file line (Direttiva CEO 048 — Bug 2).**
  The YAML handler in `check_snippet_content` used `line_no=fence_line + 1` unconditionally,
  discarding the YAML parser's `exc.problem_mark.line` offset. A syntax error on snippet line 3
  at file line 183 was reported as line 181 instead of 183.
  **Fix:** `offset = (mark.line + 1) if mark is not None else 1` where `mark = getattr(exc,
  "problem_mark", None)`. Consistent with the Python handler (`fence_line + exc.lineno`).
  Test: `test_check_snippet_yaml_absolute_line_no`.

- **Caret `^^^^` misaligns after terminal line wrap (Direttiva CEO 048 — Bug 3).**
  `_render_snippet` used a hardcoded `col_start + caret_len <= 60` threshold that did not
  account for terminal width or gutter overhead. Very long source lines (200+ chars) wrapped in
  the terminal, misplacing the caret row on the wrong visual line.
  **Fix:** `shutil.get_terminal_size(fallback=(120, 24)).columns` determines `max_src`.
  Source lines are truncated at `max_src` with a `…` suffix. Carets are only rendered when
  `col_start + caret_len <= max_src`.
  Tests: `test_render_snippet_long_line_truncated`, `test_render_snippet_caret_suppressed_when_beyond_visible`.

- **Z503 YAML multi-document snippets raise false positive (Direttiva CEO 048 — Bug 4).**
  `yaml.safe_load(snippet)` rejected YAML snippets containing `---` document separators with
  "expected a single document in the stream". Docusaurus documentation frequently shows
  frontmatter examples using `---` inside code blocks.
  **Fix:** `list(yaml.safe_load_all(snippet))` — the generator is consumed to force full parsing
  while accepting multi-document YAML streams.
  Test: `test_check_snippet_yaml_multi_doc_no_false_positive`.

#### Documentation

- **`[CLOSING PROTOCOL]` — Obsidian Memory Law codified (Direttiva CEO 049 — "The Obsidian Memory Law").**
  All three repository agent instruction files receive a `[CLOSING PROTOCOL]` section, placed
  immediately after `[MANIFESTO]`. Defines a mandatory per-repo checklist (update instructions,
  update changelogs, run staleness audit, run verification gate). Skipping any step is a Class 1
  violation (Technical Debt). Resolves the "Paradosso del Custode senza Memoria".
  Memory Law in `[POLICIES]` upgraded to "The Custodian's Contract" with the Class 1 violation
  clause and explicit "Definition of Done" invariant.

### The Intelligent Perimeter Sprint (D050 — 2026-04-25)

#### Fixed

- **Z903 false positives on engine config and infrastructure files (BUG-009 — Direttiva CEO 050 "The Intelligent Perimeter").**
  Running `zenzic check all .` from the project root emitted spurious Z903 (Unused Asset) warnings
  on `docusaurus.config.ts`, `package.json`, `pyproject.toml`, and other toolchain files.
  These files are the inputs Zenzic reads to operate; flagging them is a contradiction.
  Root cause: `find_unused_assets()` had no file-level system guardrail check — any non-Markdown
  file in `docs_root` not referenced by a page was flagged.

  **Fix — Two-layer guardrail system (L1a + L1b):**

  - **L1a — `SYSTEM_EXCLUDED_FILE_NAMES` / `SYSTEM_EXCLUDED_FILE_PATTERNS`** added to
    `src/zenzic/models/config.py`: universal toolchain files (`package.json`, `pyproject.toml`,
    `yarn.lock`, `tsconfig.json`, `uv.lock`, `eslint.config.*`, `.prettierrc*`, etc.) are
    hardcoded system guardrails, immutable by user config or CLI flags.
  - **L1b — `BaseAdapter.get_metadata_files() -> frozenset[str]`**: each adapter declares
    the engine config files it consumes (`docusaurus.config.ts` / `sidebars.ts` for Docusaurus;
    `mkdocs.yml` for MkDocs; `zensical.toml` for Zensical). `LayeredExclusionManager` stores
    and enforces them in `should_exclude_file()`. `find_unused_assets()` applies both layers
    before building the asset set. `_build_exclusion_manager` in `_shared.py` propagates
    adapter metadata to the exclusion manager at construction time.

  Rule R13 (CEO-050) codified in `[POLICIES]`: _"Never ask the user to exclude them manually."_

#### Tests

- `tests/test_exclusion.py::TestSystemFileGuardrails` — 5 new tests: exact name exclusion,
  glob pattern exclusion (`eslint.config.mjs`), `*.lock` pattern, adapter metadata L1b, and
  non-exclusion of legitimate doc files.
- `tests/test_scanner.py::test_find_unused_assets_skips_system_infrastructure_files` — L1a end-to-end.
- `tests/test_scanner.py::test_find_unused_assets_skips_adapter_metadata_files` — L1b end-to-end.

---

### Documentation as an Invariant Sprint (D051 — 2026-04-25)

#### Changed

- **`[CLOSING PROTOCOL]` Step 3 renamed to "Staleness & Testimony Audit" in all three Obsidian Ledgers.**
  Per-repo trigger checklists added: every changed function must be cross-referenced against the
  corresponding `.mdx` page before a sprint is closed.

- **Documentation Law — "The Obsidian Testimony" added to `[POLICIES]` in all three Obsidian Ledgers.**
  Mandatory trigger rules: I/O or exclusion logic changed → `configuration.mdx`; UI/CLI/module
  structure changed → `architecture.mdx`; `Zxxx` finding changed → `finding-codes.mdx`; adapter
  discovery changed → `configure-adapter.mdx`. A sprint without a Testimony check is not closed.

- **`docs/reference/finding-codes.mdx` (EN + IT) — Z502 and Z503 precision updates (zenzic-doc).**
  Z502 Technical Context now documents that word count is purely semantic: frontmatter, MDX
  comments, and HTML comments are excluded. Z503 Technical Context now documents that the reported
  line number is absolute (file-relative, not snippet-relative), enabling immediate navigation.

- **`docs/reference/configuration.mdx` (EN + IT) — New "System Guardrails (Level 1 Exclusions)" section (zenzic-doc).**
  Documents the full L1a (universal infrastructure) and L1b (adapter-declared engine configs)
  exclusion lists. The `excluded_assets` note for `_category_.json` updated: no longer required
  for Docusaurus projects (Level 1b guardrail). Existing entries are silently deduplicated.

- **`docs/how-to/configure-adapter.mdx` (EN + IT) — L1b tip box added (zenzic-doc).**
  After the adapter discovery table, a tip box informs users that engine config files are
  automatically excluded from Z903. No manual `excluded_assets` entry required.

---

### The Sovereign Root Fix (D052 — 2026-04-25)

#### Fixed

- **BUG-010: Context Hijacking via external path.**
  Running `zenzic check all /path/to/other-repo` from inside a different repository caused
  Zenzic to load the caller's `zenzic.toml` instead of the target's. Root cause:
  `find_repo_root()` always searched upward from `Path.cwd()`, ignoring the explicit target.
  Fix: `find_repo_root()` now accepts a `search_from: Path | None` parameter; `check_all()`
  derives it from the resolved target path. "The configuration follows the target, not the caller."
  — ADR-009.

- **`_apply_target()` sovereign root guard.**
  When the explicit target equalled the project's repo root, `_apply_target()` would override
  `docs_dir` to `"."` — causing the entire project root (including `blog/`, `scripts/`) to be
  scanned instead of the configured `docs_dir`. Fix: when `target == repo_root`, return config
  with the configured `docs_dir` preserved.

#### Tests Added

- `tests/test_remote_context.py` — 9 regression tests: `find_repo_root(search_from=...)` root
  isolation, `_apply_target` sovereign root guard, and end-to-end config isolation ("The Stranger"
  scenario).

---

### The Portability Invariant (D053 — 2026-04-25)

#### Fixed

- **Absolute links in `configure-adapter.mdx` (EN + IT) introduced by D051.**
  D051 used Docusaurus-style absolute paths (`/docs/reference/configuration#system-guardrails`)
  which violate Zenzic's own Z105 rule. Fixed to relative MDX paths:
  `../reference/configuration.mdx#system-guardrails`.

#### Added

- **Rule R14 — Portability is Execution-Independent.**
  Codified in `[POLICIES]`: absolute links (starting with `/`) are hard errors (Z105)
  unconditionally — even when the target file exists on disk. Z105 is a pre-resolution gate
  that fires before any filesystem check. Rationale: absolute links break portability when the
  site is hosted in a subdirectory.

- **CEO-053 regression test.**
  `tests/test_validator.py::TestAbsolutePathProhibition::test_z105_fires_even_when_target_file_exists_on_disk`
  — creates a real file, links to it with an absolute path, verifies `error_type == "ABSOLUTE_PATH"`.

---

### The Strict Perimeter Law (D054 — 2026-04-25)

#### Diagnosis

The CEO observed Z104 on `../assets/brand/svg/zenzic-badge-shield.svg` when scanning zenzic-doc
from outside the repo. Forensic investigation determined: the link is valid (the file exists at
`docs/assets/brand/svg/zenzic-badge-shield.svg`, inside `docs_root`), the Shield resolver was
already enforcing scope integrity correctly (PathTraversal Z202 fires for out-of-perimeter links),
and the Z104 was entirely a CEO-052 artifact. The "Permissive Perimeter" hypothesis was a
misdiagnosis. CEO-052 fix (already applied) eliminates the false Z104 when scanning remotely.

#### Fixed

- **BUG-011: `excluded_dirs` documented default wrongly listed `"assets"` (zenzic-doc).**
  `docs/reference/configuration.mdx` (EN + IT) stated the default was
  `["includes", "assets", "stylesheets", "overrides", "hooks"]`. The actual code default
  (`models/config.py` line 152) is `["includes", "stylesheets", "overrides", "hooks"]` — without
  `"assets"`. Adding `"assets"` to the default would break Z104 for all projects that reference
  files inside `docs/assets/`: those files would disappear from the asset index, and valid links
  to them would be falsely flagged as broken. Fixed: corrected default + tip box added explaining
  why `"assets"` is intentionally absent.

#### Added

- **Rule R15 — Scope Integrity.** Codified in `[POLICIES]`: a resolved link is valid only if its
  target is within the engine's permitted perimeter (`docs_root` + adapter-declared static dirs).
  File existence on the host filesystem outside this perimeter is irrelevant — the Shield resolver
  (PathTraversal Z202) enforces this unconditionally. This rule was already implemented; D054
  documents it as a named invariant.

- **`clean assets` command signature aligned with `check all`.**
  Added: `PATH` argument (CEO-052 sovereign root fix), `--engine`, `--exclude-dir`,
  `--include-dir`, `--quiet`. Full adapter metadata file support (L1b guardrails).

---

### The Precision Calibration Sprint (D055 — 2026-04-25)

#### Fixed

- **Z502 word count inflated by MDX SPDX comment preceding frontmatter.**
  `_visible_word_count()` ran `_FRONTMATTER_RE` (anchored to `\A`) before stripping MDX
  block-comments (`{/* … */}`). MDX files that open with a SPDX/copyright header before the
  `---` block caused the regex to miss the frontmatter block entirely, leaking all frontmatter
  key-value pairs into the prose word count. Fix: strip MDX and HTML comments first, then run
  the frontmatter regex. Pure function; original text unchanged.

- **Z105 false positive on `pathname:///` links (Docusaurus Diplomatic Courier).**
  `urlsplit("pathname:///assets/file.html")` → `scheme="pathname"`, `path="/assets/file.html"`.
  The Z105 portability gate (`parsed.path.startswith("/")`) was firing on the leading `/` of the
  URI path component — a convention artifact, not a server-root reference. Fix: gate conditioned
  on `not parsed.scheme`. Any URL with a non-empty scheme is an engine protocol, not an absolute
  path. Rule R16 "Protocol Awareness" codified.

#### Added

- Regression tests in `tests/guardians/test_precision.py` (5 tests).
- Nox development note added to `CONTRIBUTING.md` (EN) and `CONTRIBUTING.it.md` (IT).

---

### Universal Path Awareness (D056 — 2026-04-25)

#### Added

- **`zenzic score [PATH]` — optional positional argument.**
  When provided, `score` applies the CEO-052 sovereign root fix: `find_repo_root(search_from=target)`
  derives the repo root from the target path, not the CWD. Banner printed immediately before
  analysis. Scoring hint `Scoring: <path>` shown for non-CWD targets.

- **`zenzic diff [PATH]` — optional positional argument.**
  Same sovereign root semantics as `score`. Snapshot path automatically derived from `repo_root`
  (not CWD). Hint `Comparing: <path>` shown for non-CWD targets.

- Rule R17 "CLI Symmetry" codified: `score` and `diff` accept the same optional PATH argument
  as `check all`, with identical sovereign root and sandbox semantics.

---

### The Precedence Audit (D058 — 2026-04-25)

#### Changed

- **Configuration priority documentation upgraded from 3-level to 4-level.**
  `README.md` and `README.it.md` priority chain now explicitly lists CLI flags as the highest
  priority source. Previous wording omitted CLI flags entirely, misrepresenting the actual
  precedence. The authoritative chain: CLI flags > `zenzic.toml` > `[tool.zenzic]` in
  `pyproject.toml` > built-in defaults.

---

### The Law of Contemporary Testimony (D059 — 2026-04-25)

#### Changed

- **Law of Contemporary Testimony codified as mandatory operational policy.**
  All three Obsidian Ledgers (`.github/copilot-instructions.md` in core, zenzic-doc, and
  zenzic-action) updated with the new law: code and documentation are a single, indivisible
  unit of work. Step 0 "Pre-Task Alignment" added to [CLOSING PROTOCOL]. Step 3 enhanced with
  "Contemporary Check" bullets covering CLI flags, default values, architectural bugs, finding
  codes, and adapter behavior.

---

### Total CLI Symmetry (D060 — 2026-04-25)

#### Added

- **PATH argument on all `check` sub-commands.**
  `check links`, `check orphans`, `check snippets`, `check placeholders`, `check assets`, and
  `check references` now accept an optional positional `PATH` argument with sovereign root
  semantics identical to `check all`. Zenzic loads the configuration from the target, not the
  caller's CWD — enabling cross-project and monorepo usage without changing directory.

- **`init` Genesis Nomad mode.**
  `zenzic init <path>` treats the given path as the target project root. The directory is
  created (`mkdir -p`) if it does not exist. The caller's CWD is not affected. Engine
  auto-detection runs on the target directory.

#### Tests

- `test_init_nomad_writes_to_target_not_cwd` — asserts `zenzic.toml` is created at the
  target, not the CWD.
- `test_init_nomad_creates_target_directory` — asserts a non-existent nested path is created.

---

### The Genesis Nomad Enforcement (D062 — 2026-04-25)

#### Added

- **Banner & Hint Sync.** All 6 `check` sub-commands print
  `Scanning: <resolved-target>` after the Obsidian header when `PATH` is provided.
  `init` prints `Target: <resolved-path>` in Genesis Nomad mode. Operators now have
  visual confirmation of the active sovereign root before results are displayed.

- **Sovereign Root Protocol documentation** (`docs/explanation/architecture.mdx` EN + IT).
  New section documents the three-step sovereignty protocol (`find_repo_root` →
  `_apply_target` → CEO-043 sandbox guard), the Genesis Nomad invariants table, and
  the Context Hijacking problem/solution narrative.

---

### The Maturity Narrative (D061 — 2026-04-25)

#### Changed

- **Launch blog article** (`blog/2026-04-22-beyond-the-siege-zenzic-v070.mdx`) revised as a
  case study in software engineering maturity (EN + IT simultaneously).
  New sections: "Treating Documentation as Untrusted Input" (framing), "The Precision Sprint"
  (Z502 BUG-012 + Z105 BUG-013 false positive narrative), "Total CLI Symmetry: The Sovereign
  Root Protocol" (D060/D062 coverage with terminal output examples), "The Law of Contemporary
  Testimony" (CEO-059). Capabilities table updated with new rows. Test count updated
  1,195 → 1,225. CTA changed from `pip install zenzic; zenzic check all` to `uvx zenzic lab`.

---

### The Obsidian Hygiene (D063 — 2026-04-25)

#### Changed

- **Zero technical debt confirmed.** Forensic grep across all production source
  (`src/zenzic/`) for `TODO`, `FIXME`, and `HACK` markers. Every match was intentional
  production logic: the Z501 detector (`if "TODO" in line:`), rule docstrings, or example
  strings in error messages. No markers removed; none existed. The v0.7.0 "Stable" codebase
  is debt-free.

---

### Operation Matrix Laboratory (D064 — 2026-04-25)

#### Added

- **`examples/os/unix-security/`** — Red/Blue team exercise: multi-hop `../` path traversal
  targeting `/etc/passwd`, `/root/.ssh/`, `/etc/shadow`, combined with credential exposure
  across tables, blockquotes, link titles, URL parameters, and fenced code blocks.
  Exercises Z202 (PATH_TRAVERSAL) + Z201 (Shield credential detection). `check all` exits 2.

- **`examples/os/win-integrity/`** — Windows-style absolute path detection: `/C:/`, `/D:/`,
  `/Z:/`, `/UNC/server/share/`, and `file:///` link targets. All trigger Z105
  (ABSOLUTE_LINK) — environment-dependent and non-portable. `check links` exits 1.

- **`examples/rules/z100-link-graph/`** — Link graph stress test: 5-node circular broken-anchor
  network (Z102 ×13) and two links to non-existent files (Z104 ×2). `check links` exits 1.

- **`examples/rules/z200-shield/`** — Shield extreme obfuscation: Base64-encoded, percent-encoded
  (single- and double-pass), and mixed-case credential patterns. Shield normalises before
  matching — all three techniques are detected. `check references` exits 2 (BREACH).

- **`examples/rules/z400-seo/`** — SEO coverage gaps: three subdirectories with content but no
  `index.md` (Z401 ×3) and one orphan page with no inbound links (Z402 ×1). `check seo`
  exits 1.

- **`examples/rules/z500-quality/`** — Quality gate stress: three stub pages (under 50 words,
  `TODO` marker, `FIXME` marker) triggering Z501 and one page with an `@include` to a
  nonexistent snippet triggering Z503. `check quality` exits 1.

- **Acts 11–16 added to `zenzic lab`.**
  - Act 11 — Unix Security Probe (`os/unix-security`, `expected_breach=True`)
  - Act 12 — Windows Path Integrity (`os/win-integrity`, `expected_pass=False`)
  - Act 13 — Link Graph Stress (`rules/z100-link-graph`, `expected_pass=False`)
  - Act 14 — Shield Extreme (`rules/z200-shield`, `expected_breach=True`)
  - Act 15 — SEO Coverage (`rules/z400-seo`, `expected_pass=False`)
  - Act 16 — Quality Gate (`rules/z500-quality`, `expected_pass=False`)

- **`zenzic lab` UI refactored into four Rich-rendered sections.**
  `_print_act_index()` now groups acts by thematic section with an icon header:
  🛡 OS & Environment Guardrails (Acts 0–3),
  🔗 Structural & SEO Integrity (Acts 4–6),
  🏢 Enterprise Adapters & Migration (Acts 7–10),
  🔴 Red/Blue Team Matrix (Acts 11–16).
  Each section renders as a separate `ROUNDED` Rich table.

- **`examples/run_demo.sh` updated.** Section banner comments (four thematic sections)
  added. Acts 9 and 10 (previously present in `_lab.py` but absent from the script) added.
  Acts 11–16 added with correct expected exit codes (exit 2 for BREACH acts).

---

### The Range Master Protocol (D069 — 2026-04-25)

#### Changed

- **`zenzic lab` argument type changed from `int` to `str`.**
  The `ACT` argument now accepts an integer (`3`), an inclusive range (`11-16`), or the
  special value `all`. A new pure function `parse_act_range(raw: str) -> list[int]`
  performs validation and returns an ordered list of act IDs.

#### Added

- **Range execution.** `zenzic lab 11-16` runs all six Red/Blue Team Matrix acts in
  sequence and produces the multi-act Full Run Summary table via `_print_summary()`.
  Invalid range syntax (e.g. `1-x`) and out-of-bound act numbers produce an
  `ObsidianUI.print_exception_alert()` panel with a descriptive message.

- **`zenzic lab all` shorthand.** Runs all 17 acts (0–16) in ascending order.

- **Sequence header.** When more than one act is selected, the Lab prints a
  `LAB SEQUENCE: Running Acts N through M …` banner before executing.

- **`zenzic lab` section added to `docs/reference/cli.mdx` (EN + IT).**
  Documents act selection syntax (single, range, `all`), the four thematic sections,
  outcome label meanings, and usage examples. Satisfies the Law of Contemporary Testimony
  (CEO-059).

---

### The Ghost Content Fix (D072 — 2026-04-25)

#### Fixed

- **Z502 short-content pointer no longer anchors on SPDX licence headers.**
  `_first_content_line()` was implemented as a single `_FRONTMATTER_RE.match(text)` call
  anchored to `\A`. When a file opened with `<!-- SPDX-FileCopyrightText: … -->` HTML
  comments (standard REUSE practice), the frontmatter regex failed to match — causing
  `_first_content_line()` to fall back to line 1 and point the `❱` diagnostic arrow at the
  licence header instead of the first prose word.

  `_first_content_line()` is now a three-phase line-by-line walker:
  1. Skip leading HTML (`<!-- … -->`) and MDX (`{/* … */}`) comment blocks, including
     multi-line variants.
  2. Skip the YAML frontmatter block (`--- … ---`), if present after comments.
  3. Skip any blank lines between the above and the first prose word.

  The word-count logic in `_visible_word_count()` was already correct (comments stripped
  before frontmatter per D055); only the pointer was broken.

#### Tests

- **`test_short_content_pointer_skips_spdx_comments`** — "The SPDX Trap": 5 leading SPDX
  HTML comment lines + 10-line YAML frontmatter + single word `FINE`. Asserts `line_no`
  resolves to the line containing `FINE`, not to any comment or frontmatter delimiter.

---

## [0.6.1] — 2026-04-19 — Obsidian Glass [SUPERSEDED]

> ⚠ **[SUPERSEDED by v0.7.0]** — Version 0.6.1 is deprecated due to alignment issues with Docusaurus specifications and legacy terminology. All users must upgrade to v0.7.0 "Obsidian Maturity".

### Breaking Changes

- **Standalone Engine replaces Vanilla (Direttiva 037).** The `VanillaAdapter` and the
  `engine = "vanilla"` keyword have been removed. All projects must migrate to
  `engine = "standalone"`. Any `zenzic.toml` still using `engine = "vanilla"` will
  raise a `ConfigurationError [Z000]` at startup with a clear migration message.
  _Migration:_ replace `engine = "vanilla"` with `engine = "standalone"` in your
  `zenzic.toml` or `[tool.zenzic]` block.

### Added

- **Finding Codes (Zxxx) (Direttiva 036).** Every diagnostic emitted by Zenzic now
  carries a unique machine-readable identifier (e.g. `Z101 LINK_BROKEN`,
  `Z201 SHIELD_SECRET`, `Z401 MISSING_DIRECTORY_INDEX`). The full registry lives in
  `src/zenzic/core/codes.py` — the single source of truth for all codes.
- **Interactive Lab menu.** `zenzic lab` without arguments now displays the act index
  so you can choose which scenario to explore. Run `zenzic lab <N>` to execute a
  specific act (0–8). The `--act` option has been replaced by a positional argument.
- **Standalone Mode identity.** `StandaloneAdapter` is the canonical no-op engine for
  pure Markdown projects. `zenzic init` now writes `engine = "standalone"` when no
  framework config is detected.

- **`--offline` flag for Flat URL resolution.** Available on `check all`, `check links`,
  and `check orphans`. Forces all adapters to produce `.html` URLs (e.g. `guide/install.md`
  → `/guide/install.html`) instead of directory-style slugs.
- **Docusaurus v3 Multi-version support.** The `DocusaurusAdapter` now identifies
  `versions.json`, `versioned_docs/`, and versioned translations.
- **Zensical Transparent Proxy.** If `engine = "zensical"` is declared but `zensical.toml`
  is missing, the adapter automatically bridges your existing `mkdocs.yml`.
- **Version-aware Ghost Routing.** Versioned documentation paths are automatically
  classified as `REACHABLE`.
- **@site/ Alias Resolution.** Added support for the `@site/` path alias in
  `DocusaurusAdapter`, enabling project-relative links to be resolved correctly.
- **Directory Index Integrity.** New `provides_index(path)` method on the `BaseAdapter`
  protocol enables engine-aware detection of directories that lack a landing page.
  The `MISSING_DIRECTORY_INDEX` finding (severity: `info`) is emitted by `zenzic check all`
  for every subdirectory that contains Markdown sources but no engine-provided index entry
  — preventing hierarchical 404s before deployment.
- **Sentinel Banner Notifications.** New status messages for **Offline Mode** and
  **Proxy Mode** activation.

### Fixed

- **Guardians Audit: Official Specs Alignment.**
  - **Docusaurus Versioning:** Fixed "latest" version (first entry in `versions.json`) URL
    mapping to exclude the version label prefix, matching official Docusaurus behavior.
    Previously every versioned file received a `/version/` prefix, causing false positive
    broken-link reports for all latest-version pages.
  - **Docusaurus Slugs:** Absolute frontmatter slugs (e.g. `slug: /my-path`) are now
    correctly prepended with `routeBasePath` (e.g. `/docs/my-path/`), aligning with
    the Docusaurus `normalizeUrl([versionMetadata.path, docSlug])` specification.
  - **Smart File Collapsing:** `isCategoryIndex` logic now mirrors Docusaurus exactly:
    `README.md`, `INDEX.md` (case-insensitive), and `{FolderName}/{FolderName}.md`
    collapse to the parent directory URL, preventing false positive broken-link reports
    for valid category landing page conventions.
  - **`@site/` Alias Resolution:** The `InMemoryPathResolver` now resolves `@site/`
    links against the correct `repo_root` boundary instead of escaping via `../`,
    eliminating spurious `PathTraversal` errors for all Docusaurus project-relative links.
- **Metadata Integrity.** Corrected version string alignment in `CITATION.cff` and `pyproject.toml`.
- **Docusaurus routeBasePath default.** Restored `docs` as the default URL prefix for
  Docusaurus projects to match official engine behavior.

- **Bilingual Documentation Parity.** Full EN/IT documentation coverage for all
  v0.6.1 features across the Architecture, Engine, and Command guides.

## [0.6.1rc2] — 2026-04-16 — Obsidian Bastion (Hardened)

### SECURITY: Operation Obsidian Stress Findings

- **Shield: Unicode format character bypass (ZRT-006).** Zero-width Unicode
  characters (ZWJ U+200D, ZWNJ U+200C, ZWSP U+200B) inserted mid-token could
  break regex matching. The normalizer now strips all Unicode category Cf
  characters before scanning.
- **Shield: HTML entity obfuscation bypass (ZRT-006).** HTML character
  references (`&#65;&#75;` → `AK`) could hide credential prefixes. The
  normalizer now decodes `&#NNN;`/`&#xHH;` entities via `html.unescape()`.
- **Shield: comment-interleaving bypass (ZRT-007).** HTML comments
  (`<!-- -->`) and MDX comments (`{/* */}`) inserted mid-token could break
  pattern matching. The normalizer now strips both comment forms.
- **Shield: cross-line split-token detection (ZRT-007).** Added a 1-line
  lookback buffer via `scan_lines_with_lookback()` to detect secrets split
  across two consecutive lines (e.g. YAML folded scalars). Suppresses duplicates
  via previous-line seen set.

### Added

- **`--format json` on individual check commands.** `check links`, `check orphans`,
  `check snippets`, `check references`, and `check assets` now accept `--format json`
  with a uniform `findings`/`summary` schema. Exit codes are preserved in JSON mode.
  ([#55](https://github.com/PythonWoods/zenzic/pull/55) — contributed by [@xyaz1313](https://github.com/xyaz1313))
- **Shield: GitLab Personal Access Token detection.** The credential scanner now
  detects `glpat-` tokens (9 credential families total).
  ([#57](https://github.com/PythonWoods/zenzic/pull/57) — contributed by [@gtanb4l](https://github.com/gtanb4l))

### Fixed

- **JSON exit-code asymmetry in `check orphans` and `check assets`.** Both commands
  now distinguish `error` vs `warning` severity before deciding exit codes, consistent
  with `check references` and `check snippets`. Previously, any finding (including
  warnings) triggered Exit 1 in JSON mode.

## [0.6.1rc1] — 2026-04-15 — Obsidian Bastion

### Breaking Changes

- **Removed `zenzic serve` command.** Zenzic is now 100% subprocess-free,
  focusing exclusively on static source analysis. To preview your documentation,
  use your engine's native command: `mkdocs serve`, `docusaurus start`, or
  `zensical serve`. This removal eliminates the sole exception to Pillar 2
  (No Subprocess) and completes the architectural purity of the framework.
- **MkDocs plugin moved to `zenzic.integrations.mkdocs`** — Previously at
  `zenzic.plugin`. Update your MkDocs `mkdocs.yml` to reinstall the package;
  the plugin is now auto-discovered via the `mkdocs.plugins` entry point.
  Requires `pip install "zenzic[mkdocs]"`.

### Added

- **Layered Exclusion Manager** — New 4-level exclusion hierarchy (System
  Guardrails > Forced Inclusions + VCS > Config > CLI). Pure-Python gitignore
  parser (`VCSIgnoreParser`) with pre-compiled regex patterns. New config fields:
  `respect_vcs_ignore`, `included_dirs`, `included_file_patterns`.
- **Universal Discovery** — Zero `rglob` calls in the codebase. All file
  iteration flows through `walk_files` / `iter_markdown_sources` from
  `discovery.py`. Mandatory `exclusion_manager` parameter on all scanner and
  validator entry points — no Optional, no fallbacks.
- **CLI Exclusion Flags** — `--exclude-dir` and `--include-dir` repeatable
  options on all check commands, `score`, and `diff`.
- **Adapter Cache** — Module-level cache keyed by `(engine, docs_root,
  repo_root)`. Single adapter instantiation per CLI session.
- **F4-1 Jailbreak Protection** — `_validate_docs_root()` rejects `docs_dir`
  paths that escape the repository root (Blood Sentinel Exit 3).
- **F2-1 Shield Hardening** — Lines exceeding 1 MiB are silently truncated
  before regex matching to prevent ReDoS.
- **`zenzic.integrations` namespace** — MkDocs plugin relocated from
  `zenzic.plugin` to `zenzic.integrations.mkdocs`. Registered as an official
  `mkdocs.plugins` entry point. Core is now free of any engine-specific
  imports. Install the extra: `pip install "zenzic[mkdocs]"`.

### Changed

- **BREAKING (Alpha):** `exclusion_manager` parameter is now mandatory on
  `walk_files`, `iter_markdown_sources`, `generate_virtual_site_map`,
  `check_nav_contract`, and all scanner functions. No backward-compatible
  `None` default.

## [0.6.0a2] — 2026-04-13 — Obsidian Glass (Alpha 2)

### Added

- **Glob Pattern Support for `excluded_assets`** — `excluded_assets` entries
  are now matched via `fnmatch` (glob syntax: `*`, `?`, `[]`, `**`).  Literal
  paths continue to work as before.  This brings `excluded_assets` in line
  with `excluded_build_artifacts` and `excluded_file_patterns`, giving the
  entire exclusion API a single, consistent language.
- **`base_url` in `[build_context]`** — New optional field that lets users
  declare the site’s base URL explicitly.  When set, the Docusaurus adapter
  skips static extraction from `docusaurus.config.ts`, eliminating the
  “dynamic patterns” fallback warning for configs that use `async`,
  `import()`, or `require()`.
- **Metadata-Driven Routing** — New `RouteMetadata` dataclass and
  `get_route_info()` method on the `BaseAdapter` protocol. All four adapters
  (Vanilla, MkDocs, Docusaurus, Zensical) implement the new API. `build_vsm()`
  prefers the metadata-driven path when available, falling back to the legacy
  `map_url()` + `classify_route()` pair for third-party adapters.
- **Centralized Frontmatter Extraction** — Engine-agnostic utilities in
  `_utils.py`: `extract_frontmatter_slug()`, `extract_frontmatter_draft()`,
  `extract_frontmatter_unlisted()`, `extract_frontmatter_tags()`, and
  `build_metadata_cache()` for single-pass eager harvesting of YAML
  frontmatter across all Markdown files.
- **`FileMetadata` dataclass** — Structured representation of per-file
  frontmatter: `slug`, `draft`, `unlisted`, `tags`.
- **Shield IO Middleware** — `safe_read_line()` scans every frontmatter line
  through the Shield before any parser sees it. `ShieldViolation` exception
  provides structured error with `SecurityFinding` payload.
- **Protocol Compliance Tests** — 43 new tests in `test_protocol_evolution.py`:
  `runtime_checkable` protocol validation, `RouteMetadata` invariants,
  `get_route_info()` contract tests for all adapters, Hypothesis stress tests
  with extreme paths, pickle safety, frontmatter extraction, Shield middleware,
  and VanillaAdapter warning-free operation.

### Changed

- **BREAKING: `excluded_assets` uses fnmatch** — All entries are now
  interpreted as glob patterns.  Plain literal paths still match (they are
  valid patterns), but patterns like `**/_category_.json` or `assets/brand/*`
  are now supported natively.  The previous set-subtraction implementation
  has been removed.

### Fixed

- **Docusaurus “dynamic patterns” warning emitted twice** — When
  `base_url` is declared in `zenzic.toml`, the adapter no longer calls
  `_extract_base_url()`, suppressing the duplicate warning entirely.

## [0.6.0a1] — 2026-04-12 — Obsidian Glass

> **Alpha 1 of the v0.6 series.** Zenzic evolves from a MkDocs-aware linter into
> an **Analyser of Documentation Platforms**. This release introduces the
> Docusaurus v3 engine adapter — the first non-MkDocs/Zensical adapter — and
> marks the beginning of the Obsidian Bridge migration strategy.

### Added

- **Docusaurus v3 Adapter (Full Spec)**: New engine-agnostic adapter with
  static-AST-like parsing for `docusaurus.config.ts/js`. Satisfies the
  `BaseAdapter` protocol. Handles `.md` and `.mdx` source files,
  auto-generated sidebar mode (all files `REACHABLE`), Docusaurus i18n
  geography (`i18n/{locale}/docusaurus-plugin-content-docs/current/`),
  Ghost Route detection for locale index pages, and `_`-prefixed
  file/directory exclusion (`IGNORED`). Registered as built-in adapter with
  entry-point `docusaurus = "zenzic.core.adapters:DocusaurusAdapter"`.
  - **`baseUrl` extraction**: Multi-pattern static parser supporting
    `export default`, `module.exports`, and `const`/`let` assignment patterns.
    JS/TS comments are stripped before extraction. No Node.js subprocess
    (Pillar 2 compliance).
  - **`routeBasePath` extraction**: Automatic detection of `routeBasePath`
    from Docusaurus presets and plugin blocks (e.g.
    `@docusaurus/preset-classic`). Supports empty string (docs at site root).
  - **Slug Support**: Markdown frontmatter `slug:` overrides are now correctly
    mapped into the VSM. Absolute slugs (`/custom-path`) replace the full URL;
    relative slugs replace the last path segment.
  - **Dynamic Config Detection**: Intelligent detection of async config
    creators, `import()`/`require()` calls, and function-based exports. Falls
    back to `baseUrl='/'` with a user warning — never crashes, never guesses.
- **`from_repo()` factory hook** for `DocusaurusAdapter`: Auto-discovers
  `docusaurus.config.ts` or `.js` and constructs the adapter with the correct
  `baseUrl` and `routeBasePath`.
- **Improved i18n Topology**: Native mapping for Docusaurus `i18n/` directory
  structure and locale-specific route resolution.

### Testing

- **`tests/test_docusaurus_adapter.py` — 65 tests across 12 test classes.**
  Full coverage of the Docusaurus adapter refactor: config parsing (CFG-01..07),
  `routeBasePath` extraction (RBP-01), frontmatter slug support (SLUG-01),
  dynamic config detection, comment stripping, `from_repo()` integration,
  URL mapping regression, and route classification regression.
