<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [0.6.1a1] — 2026-04-14 — Obsidian Bastion

### Breaking Changes

- **Removed `zenzic serve` command.** Zenzic is now 100% subprocess-free,
  focusing exclusively on static source analysis. To preview your documentation,
  use your engine's native command: `mkdocs serve`, `docusaurus start`, or
  `zensical serve`. This removal eliminates the sole exception to Pillar 2
  (No Subprocess) and completes the architectural purity of the framework.

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

### Changed

- **BREAKING (Alpha):** `exclusion_manager` parameter is now mandatory on
  `walk_files`, `iter_markdown_sources`, `generate_virtual_site_map`,
  `check_nav_contract`, and all scanner functions. No backward-compatible
  `None` default.

## [0.6.0a2] — 2026-04-13 — Obsidian Glass

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

## [0.5.0a5] — 2026-04-09 — The Sentinel Codex

> **Alpha 5 Release.** Visual-language overhaul: Sentinel Style Guide,
> card-grid refactoring, admonition/icon normalisation, 102 strategic anchor IDs,
> CSS card hover effects, and fully automated screenshot generation pipeline.
> Legacy PDF template removed. Changelog tracking stabilised. E2E CLI security
> tests added; `--exit-zero` bug fixed (exits 2/3 are now unconditionally
> non-suppressible, matching the documented contract).

### Added

- **Sentinel Style Guide** — canonical visual-language reference
  (`docs/internal/style-guide-sentinel.md` + Italian mirror) defining card grids,
  admonition types, icon vocabulary, and anchor-ID conventions.

- **Automated screenshot generation — Blood & Circular SVGs.**
  `scripts/generate_docs_assets.py` now generates all five documentation
  screenshots: `screenshot.svg`, `screenshot-hero.svg`, `screenshot-score.svg`,
  `screenshot-blood.svg`, and `screenshot-circular.svg`. The Blood Sentinel and
  Circular Link SVGs were previously hand-crafted static assets; they are now
  deterministically generated from dedicated sandbox fixtures
  (`tests/sandboxes/screenshot_blood/`, `tests/sandboxes/screenshot_circular/`).

- **CHANGELOG.it.md bumpversion tracking.** Italian changelog added to
  `[tool.bumpversion.files]` in `pyproject.toml`, ensuring version headings
  stay synchronised across both changelogs during `bump-my-version` runs.

### Fixed

- **`--exit-zero` no longer suppresses security exits in `check all`.**
  Exit codes 2 (Shield breach) and 3 (Blood Sentinel) were guarded by
  `not effective_exit_zero` in `check all`, contradicting the documented
  contract ("never suppressed by `--exit-zero`"). The guards have been
  removed — exits 2 and 3 are now unconditional, matching `check links`
  and `check references`.

### Testing

- **`tests/test_cli_e2e.py` — 8 end-to-end CLI security tests.**
  Full-pipeline tests (no mocks) exercising the exit-code contract:
  - `TestBloodSentinelE2E` (2 tests) — Blood sandbox triggers Exit 3;
    `--exit-zero` does NOT suppress it.
  - `TestShieldBreachE2E` (2 tests) — fake AWS key triggers Exit 2;
    `--exit-zero` does NOT suppress it.
  - `TestExitZeroContractE2E` (3 tests) — broken link exits 1;
    `--exit-zero` suppresses to 0; clean sandbox exits 0.
  - `TestExitCodePriorityE2E` (1 test) — when both security_incident
    and security_breach coexist, Exit 3 wins.
  Closes gap: `docs/internal/arch_gaps.md` § "Security Pipeline Coverage".

### Changed

- **Card Grid Refactoring.** Documentation pages standardised to Material for
  MkDocs grid syntax (`:material-*:` icons, consistent column layouts).

- **Admonition Normalisation.** Ad-hoc callout styles replaced with canonical
  admonition types (`tip`, `warning`, `info`, `example`) per the Sentinel
  Style Guide.

- **Icon Normalisation.** Non-Material icons purged; all icons standardised to
  the `:material-*:` icon set.

- **102 Strategic Anchor IDs** placed across 70 documentation files for
  stable deep-linking.

- **CSS Card Overrides.** Hover effects and consistent card styling added via
  `docs/assets/stylesheets/`.

### Removed

- **`docs/assets/pdf_cover.html.j2`** — legacy Jinja2 PDF cover template.
  Orphan artifact with no build-pipeline reference; removed to reduce
  maintenance surface.

---

## [0.5.0a4] — 2026-04-08 — The Hardened Sentinel: Security & Integrity

> **Alpha 4 Release.** Four confirmed vulnerabilities closed (ZRT-001–004), three
> new hardening pillars added (Blood Sentinel, Graph Integrity, Hex Shield), and
> full bilingual documentation parity achieved. Pending manual review before
> Release Candidate promotion.
>
> Branch: `fix/sentinel-hardening-v0.5.0a4`

### Added

- **Graph Integrity — circular link detection.** Zenzic now pre-computes a cycle
  registry (Phase 1.5) via iterative depth-first search (Θ(V+E)) over the resolved
  internal link graph. Any link whose target belongs to a cycle emits a `CIRCULAR_LINK`
  finding at severity `info`. Mutual navigation links (A ↔ B) are valid documentation
  structure and are expected; the finding is advisory only — it never affects exit
  codes in normal or `--strict` mode. O(1) per-query in Phase 2. Ghost Routes
  (plugin-generated canonical URLs without physical source files) are correctly
  excluded from the cycle graph and cannot produce false positives.

- **`INTERNAL_GLOSSARY.toml`** — bilingual EN↔IT term registry (15 entries) for
  consistent technical vocabulary across English and Italian documentation. Covers
  core concepts: Safe Harbor, Ghost Route, Virtual Site Map, Two-Pass Engine, Shield,
  Blood Sentinel, and more. Maintained by S-0. All terms marked `stable = true`
  require an ADR before renaming.

- **Bilingual documentation parity.** `docs/checks.md` and `docs/it/checks.md`
  updated with Blood Sentinel, Circular Links, and Hex Shield sections.
  `CHANGELOG.it.md` created. Full English–Italian parity enforced per the
  Bilingual Parity Protocol.

### ⚠️ Security

- **Blood Sentinel — system-path traversal classification (Exit Code 3).**
  `check links` and `check all` now classify path-traversal findings by intent.
  An href that escapes `docs/` and resolves to an OS system directory (`/etc/`,
  `/root/`, `/var/`, `/proc/`, `/sys/`, `/usr/`) is classified as
  `PATH_TRAVERSAL_SUSPICIOUS` with severity `security_incident` and triggers
  **Exit Code 3** — a new, dedicated exit code reserved for host-system probes.
  Exit 3 takes priority over Exit 2 (credential breach) and is never suppressed
  by `--exit-zero`. Plain out-of-bounds traversals (e.g. `../../sibling-repo/`)
  remain `PATH_TRAVERSAL` at severity `error` (Exit Code 1).

- **Hex Shield — hex-encoded payload detection.**
  A new built-in Shield pattern `hex-encoded-payload` detects runs of three or
  more consecutive `\xNN` hex escape sequences (`(?:\\x[0-9a-fA-F]{2}){3,}`).
  The `{3,}` threshold avoids false positives on single hex escapes common in
  regex documentation. Findings exit with code 2 (Shield, non-suppressible)
  and apply to all content streams including fenced code blocks.

- **[ZRT-001] Shield Blind Spot — YAML Frontmatter Bypass (CRITICAL).**
  `_skip_frontmatter()` was used as the Shield's line source, silently
  discarding every line in a file's YAML `---` block before the regex
  engine ran. Any key-value pair (`aws_key: AKIA…`, `github_token: ghp_…`)
  was invisible to the Shield and would have exited `zenzic check all` with
  code `0`.
  **Fix:** The Shield stream now uses a raw `enumerate(fh, start=1)` —
  every byte of the file is scanned. The content stream (ref-def harvesting)
  still uses `_iter_content_lines()` with frontmatter skipping to avoid
  false-positive link findings from metadata values. This is the
  **Dual-Stream** architecture described in the remediation directives.
  *Exploit PoC confirmed via live script: 0 findings before fix, correct
  detection of AWS / OpenAI / Stripe / GitHub tokens after fix.*

- **[ZRT-002] ReDoS + ProcessPoolExecutor Deadlock (HIGH).**
  A `[[custom_rules]]` pattern like `^(a+)+$` passed the eager
  `_assert_pickleable()` check (pickle is blind to regex complexity) and
  was distributed to worker processes. The `ProcessPoolExecutor` had no
  timeout: any worker hitting a ReDoS-vulnerable pattern on a long input
  line hung permanently, blocking the entire CI pipeline.
  **Two defences added:**
  — *Canary (prevention):* `_assert_regex_canary()` stress-tests every
    `CustomRule` pattern against three canary strings (`"a"*30+"b"`, etc.)
    under a `signal.SIGALRM` watchdog of 100 ms at `AdaptiveRuleEngine`
    construction time. ReDoS patterns raise `PluginContractError` before the
    first file is scanned. (Linux/macOS only; silently skipped on Windows.)
  — *Timeout (containment):* `ProcessPoolExecutor.map()` replaced with
    `submit()` + `future.result(timeout=30)`. A timed-out worker produces a
    `Z009: ANALYSIS_TIMEOUT` `RuleFinding` instead of hanging the scan.
    The new `_make_timeout_report()` and `_make_error_report()` helpers
    ensure clean error surfacing in the standard findings UI.
  *Exploit PoC confirmed: `^(a+)+$` on `"a"*30+"b"` timed out in 5 s;
  both defences independently prevent scan lock-up.*

- **[ZRT-003] Split-Token Shield Bypass — Markdown Table Obfuscation (MEDIUM).**
  The Shield's `scan_line_for_secrets()` ran each raw line through the
  regex patterns once. A secret fragmented across backtick spans and a
  string concatenation operator (`` `AKIA` + `1234567890ABCDEF` ``) inside
  a Markdown table cell was never reconstructed, so the 20-character
  contiguous `AKIA[0-9A-Z]{16}` pattern never matched.
  **Fix:** New `_normalize_line_for_shield()` pre-processor in `shield.py`
  unwraps backtick spans, removes concatenation operators, and collapses
  table pipes before scanning. Both the raw line and the normalised form are
  scanned; a `seen` set prevents duplicate findings when both forms match.

### Changed

- **[ZRT-004] Context-Aware VSM Resolution — `VSMBrokenLinkRule` (MEDIUM).**
  `_to_canonical_url()` was a `@staticmethod` without access to the source
  file's directory. Relative hrefs containing `..` segments (e.g.
  `../../c/target.md` from `docs/a/b/page.md`) were resolved as if they
  originated from the docs root, producing false negatives: broken relative
  links in nested files were silently passed.
  **Fix:** New `ResolutionContext` dataclass (`docs_root: Path`,
  `source_file: Path`) added to `rules.py`. `BaseRule.check_vsm()` and
  `AdaptiveRuleEngine.run_vsm()` accept `context: ResolutionContext | None`
  (default `None` — fully backwards-compatible). `_to_canonical_url()` is
  now an instance method that resolves `..` segments via `os.path.normpath`
  relative to `context.source_file.parent` when context is provided, then
  re-maps to a docs-relative posix path before the clean-URL transformation.
  Paths that escape `docs_root` return `None` (Shield boundary respected).

- **[GA-1] Telemetry / Executor Worker Count Synchronisation.**
  `ProcessPoolExecutor(max_workers=workers)` used the raw `workers` sentinel
  (may be `None`) while the telemetry reported `actual_workers` (always an
  integer). Both now use `actual_workers`, eliminating the divergence.

- **Stream Multiplexing** (`scanner.py`). `ReferenceScanner.harvest()`
  now explicitly documents its two-stream design: **Shield stream** (all
  lines, raw `enumerate`) and **Content stream** (`_iter_content_lines`,
  frontmatter/fence filtered). Comments updated to make the architectural
  intent visible to future contributors.

- **[Z-SEC-002] Secure Breach Reporting Pipeline (Commit 2).**
  Four structural changes harden the path from secret detection to CI output:

  — *Breach Panel (`reporter.py`):* findings with `severity="security_breach"`
  render as a dedicated high-contrast panel (red on white) positioned before
  all other findings. Surgical caret underlines (`^^^^`) are positioned using
  the `col_start` and `match_text` fields added to `SecurityFinding`.

  — *Surgical Secret Masking — `_obfuscate_secret()`:* raw secret material is
  never passed to Rich or CI log streams. The function partially redacts
  credentials (first 4 + last 4 chars; full redaction for strings ≤ 8 chars)
  and is the **sole authorised path** for rendering secret values in output.

  — *Bridge Function — `_map_shield_to_finding()` (`scanner.py`):* a single
  pure function is the only authorised conversion point between the Shield
  detection layer and `SentinelReporter`. Extracted as a standalone function
  so that mutation testing can target it directly and unambiguously.

  — *Post-Render Exit 2 (`cli.py`):* the security hard-stop is now applied
  **after** `reporter.render()`, guaranteeing the full breach panel is
  visible in CI logs before the process exits with code 2.

### Testing

- **`tests/test_redteam_remediation.py`** — 25 new tests organised in four
  classes, one per ZRT finding:
  - `TestShieldFrontmatterCoverage` (4 tests) — verifies Shield catches
    AWS, GitHub, and multi-pattern secrets inside YAML frontmatter; confirms
    correct line-number reporting; guards against false positives on clean
    metadata.
  - `TestReDoSCanary` (6 tests) — verifies canary rejects classic `(a+)+`
    and alternation-based `(a|aa)+` ReDoS patterns at engine construction;
    confirms safe patterns pass; verifies non-`CustomRule` subclasses are
    skipped.
  - `TestShieldNormalizer` (8 tests) — verifies `_normalize_line_for_shield`
    unwraps backtick spans, removes concat operators, collapses table pipes;
    verifies `scan_line_for_secrets` catches split-token AWS key; confirms
    deduplication prevents double-emit when raw and normalised both match.
  - `TestVSMContextAwareResolution` (7 tests) — verifies multi-level `..`
    resolution from nested dirs, single `..` from subdirs, absent-from-VSM
    still emits Z001, path-traversal escape returns no false Z001, backwards
    compatibility without context, `index.md` directory mapping, and
    `run_vsm` context forwarding.
- **`tests/test_rules.py`** — `_BrokenVsmRule.check_vsm()` updated to
  accept the new `context=None` parameter (API compatibility fix).
- **731 tests pass.** Zero regressions. `pytest --tb=short` — all green.

- **`TestShieldReportingIntegrity` — Mutation Gate (Commit 3, Z-TEST-003).**
  Three mandatory tests serving as permanent Mutation Gate guards for the
  security reporting pipeline:
  - *The Invisible:* `_map_shield_to_finding()` must always emit
    `severity="security_breach"` — a downgrade to `"warning"` is caught
    immediately (`assert 'warning' == 'security_breach'`).
  - *The Amnesiac:* `_obfuscate_secret()` must never return the raw secret
    — removing the redaction logic is caught immediately
    (`assert raw_key not in output`).
  - *The Silencer:* `_map_shield_to_finding()` must never return `None` —
    a bridge function that discards findings is caught immediately
    (`assert result is not None`).

  **Manual verification (The Sentinel's Trial):** all three mutants were
  applied by hand and confirmed killed. `mutmut` v3 automatic reporting was
  blocked by an editable-install interaction (see `mutmut_pytest.ini`); manual
  verification accepted per Architecture Lead authorisation (Z-TEST-003).
  **28 tests in `test_redteam_remediation.py`, all green.**

### Internal

- **CI/CD deployment pipeline fixed for Node.js 24.**
  `cloudflare/wrangler-action@v3` calls `npx wrangler` without `--yes`; npm 10+
  on Node.js 24 GitHub Actions runners blocks non-interactive prompts, causing the
  Cloudflare Pages deploy to fail. Fix: pre-install `wrangler@latest` globally
  before the action runs so npx finds the binary in PATH without downloading.
  `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` silences the Node.js 20 deprecation
  warning ahead of the June 2026 forced migration. Tracked in `arch_gaps.md`.
  Branch: `fix/v050a4-infra-alignment`.

## [0.5.0a3] — 2026-04-03 — The Sentinel: Aesthetic Sprint, Parallel Anchors & Agnostic Target

> **Sprint 13 + 14 + 15.** Three tracks delivered in one tag.
> Track A — Performance & SDK: deterministic two-phase anchor validation, `zenzic.rules` public
> namespace, plugin scaffold command, Z001/Z002 split.
> Track B — Aesthetic & DX: Sentinel Palette with Slate/Indigo/Rose/Amber color identity,
> unified banner telemetry, agnostic target mode (`zenzic check all README.md` or
> `zenzic check all content/`), `.pre-commit-hooks.yaml`, native Material header via
> `MutationObserver`, and two new example projects.
> Track C — The Breathing Sentinel: native `col_start`/`match_text` propagation replacing
> fragile regex workarounds, surgical caret rendering, traceback gutter with 2-space
> padding, vertical breathing between findings, and a dedicated success-state panel.

### Added

- **`src/zenzic/ui.py` — Sentinel Palette** — new module centralising all color and emoji
  constants for the Sentinel report engine.  Ships 8 named constants (`INDIGO`, `SLATE`,
  `ROSE`, `AMBER`, `STYLE_BRAND`, `STYLE_DIM`, `STYLE_ERR`, `STYLE_WARN`), the
  `make_sentinel_header()` banner factory, and the `emoji()` helper with `--no-color` guard.

- **Agnostic Target Support — `PATH` argument on `check all`** — `zenzic check all`
  accepts an optional positional `PATH` argument scoping the audit to:
  - **Single file** — `zenzic check all README.md` audits exactly one Markdown file;
    banner reports `1 file (1 docs, 0 assets)`.
  - **Custom directory** — `zenzic check all content/` patches `docs_dir` at runtime
    and audits the entire subdirectory; banner reports `./content/`.
  - `VanillaAdapter` is selected automatically when the target lies outside the
    configured `docs_dir` (e.g. a root-level `README.md`).
  - `_resolve_target()` — resolves absolute/relative paths, checks for `.md` extension
    on files, exits 1 with a clear error on path-not-found.
  - `_apply_target()` — returns `(patched_config, single_file_or_None, docs_root, hint)`;
    patches `config.docs_dir` via `model_copy()` (Pydantic v2, no mutation).
  - Post-hoc filter: after `_to_findings()`, results are filtered to `rel_path == target`
    in single-file mode so no off-target findings bleed through.

- **Target hint in banner** — `make_sentinel_header()` accepts `target: str | None`;
  when set, the hint (e.g. `./README.md`, `./content/`) appears in the meta line
  between the engine name and the file count.

- **`.pre-commit-hooks.yaml`** — first-class pre-commit hook definitions shipped in the
  repository root, enabling `repo: https://github.com/PythonWoods/zenzic` in any
  `.pre-commit-config.yaml`.

- **`examples/single-file-target/`** — new example demonstrating single-file audit
  (`zenzic check all README.md`); expected exit 0.

- **`examples/custom-dir-target/`** — new example demonstrating directory-target audit
  (`zenzic check all content/`); expects exit 0 with `./content/ • 2 files`.

- **`run_demo.sh` Act 4 & 5** — Philosophy Tour extended with two new acts validating
  the single-file and custom-directory target examples automatically.

- **`zenzic.rules` public namespace** — stable import path for plugin authors:
  `BaseRule`, `RuleFinding`, `CustomRule`, `Violation`, `Severity` (#13).

- **`run_rule()` test helper** — single-call rule validation for plugin authors,
  no engine setup required (#13).

- **Z002 orphan-link warning** — `VSMBrokenLinkRule` now distinguishes between
  broken links (Z001 error) and links to orphan pages (Z002 warning) (#6).

- `zenzic init --plugin <name>` command scaffolds a plugin package with:
  - `pyproject.toml` preconfigured for `zenzic.rules` entry-points
  - `src/<module>/rules.py` module-level `BaseRule` template
  - minimal docs fixture and `zenzic.toml` so `zenzic check all` can run

- **Smart Initialization — `zenzic init --pyproject`** — when `pyproject.toml`
  exists, `zenzic init` interactively asks whether to embed configuration as a
  `[tool.zenzic]` table instead of creating a standalone `zenzic.toml`.  Pass
  `--pyproject` to skip the prompt.  `--force` overwrites an existing
  `[tool.zenzic]` section.  Engine auto-detection works in both modes.

- `examples/plugin-scaffold-demo/` — living scaffold output fixture for SDK
  integration checks and contributor onboarding.

- Anchor torture regression test with **1000 cross-linked files** to guarantee
  no race-induced false positives in anchor validation.

### Changed

- **Native Data Propagation — "The Breathing Sentinel"** (`reporter.py`,
  `validator.py`, `scanner.py`, `rules.py`, `cli.py`) — replaced the fragile
  `_extract_token()` regex workaround with native `col_start`/`match_text`
  propagation from every checker through the full pipeline to the reporter.
  Every regex match site now captures `m.start()` and `m.group()` at detection
  time and stores them in the finding dataclass — no reverse-engineering from
  error messages.

- **`LinkInfo` NamedTuple** (`validator.py`) — new type
  `(url, lineno, col_start, match_text)` replacing plain `tuple[str, int]`
  throughout the validator pipeline.  `extract_links()` and
  `extract_ref_links()` now return `list[LinkInfo]`.

- **Widened dataclasses** — `LinkError`, `PlaceholderFinding`, `RuleFinding`,
  `Violation`, and `Finding` all gained `col_start: int = 0` and
  `match_text: str = ""` fields, propagated end-to-end.

- **Traceback Gutter** (`reporter.py`) — increased gutter padding to 2 spaces
  around the vertical line: `16  ❱  code` / `16  │  code`.

- **Vertical Breathing** (`reporter.py`) — empty `Text()` lines inserted
  between different findings in the same file, before/after code snippets,
  after file-separator rules, and before the verdict line.

- **Success State** (`reporter.py`) — when all checks pass, the panel renders
  a dedicated all-clear layout: telemetry → rule → elegant
  `✔ All checks passed. Your documentation is secure.` message.

- **Surgical Caret Rendering** (`reporter.py`) — `_render_snippet()` uses
  native `col_start`/`match_text` to render precise `^^^^` caret underlines;
  carets are suppressed when `col_start + len(match_text) > 60` (wrapping
  guard) or when `match_text` is empty (no position data available).

- **Removed `_extract_token()`** (`reporter.py`) — deleted the `_TOKEN_RE`
  regex pattern and `_extract_token()` function; removed `import re` from the
  module.  The reporter no longer guesses token positions from message strings.

- **Sentinel Gutter Reporter** (`reporter.py`) — source-line context block uses
  the Sentinel Palette consistently:
  - `│` separators and line numbers rendered in `SLATE`
  - Numeric counts (`N errors`, `N warnings`, `N files`) rendered in `INDIGO`
  - Error row icon and label rendered in `ROSE`
  - Warning row icon and label rendered in `AMBER`
  - All bold removed from report numbers ("evitiamo grassetto" standard).

- **Unified banner counter** — `make_sentinel_header()` emits a single
  `N files (D docs, A assets)` breakdown replacing the previous separate
  `N docs • N assets` counters.  `mkdocs.yml` and other engine config files
  at project root are included in the docs count.  Format:
  `engine • [target •] N files (D docs, A assets) • T.Ts`.

- **`has_failures` logic** (`check_all`) — changed from `results.failed` (raw
  pre-filter counts) to `(errors > 0) or (effective_strict and warnings > 0)`,
  where `errors` and `warnings` are derived from the post-hoc filtered
  `all_findings` list.  Fixes false exit-1 when a target-mode scan filters
  findings to zero but the full scan found off-target issues (e.g. `zenzic.toml`
  listed as unused asset when `docs_dir` is patched to `.`).

- **CLI help strings audited** — five stale or incorrect help strings corrected:
  - `PATH` argument: now documents both file and directory targets with examples
  - `check all --strict`: was "validate external URLs" (wrong); now "treat warnings
    as errors (exit non-zero on any warning)"
  - `check all`, `score`, `diff` docstrings updated with target mode notes
  - `score --strict` / `diff --strict`: was vague "Run link check in strict mode";
    now "Also validate external HTTP/HTTPS links (slower; requires network)"
  - `serve --engine`: added `vanilla` to the engine list

- **Native Material header** (`docs/overrides/main.html`) — `source.html` partial
  deleted; version is injected into Material's own source facts `<ul>` via a
  `MutationObserver` snippet in `main.html` (zero template override, single header
  row: 🏷 0.5.0a3 ☆ stars ψ forks).

- **Badge rebranding** — `cacheBuster` parameter in status badge URLs updated from
  `v050` to `sentinel-a3` in `README.md` and `README.it.md`; badges rendered
  as multi-line `<a>\n  <img>\n</a>` for readability.

- **"Sentinel in Action" section** — three-card visual tour grid added to
  `docs/index.md` and `docs/it/index.md` illustrating the gutter reporter,
  Zenzic Shield, and quality score output.

- **Script consolidation** — `scripts/generate_screenshot.py` deleted;
  its functionality merged into `scripts/generate_docs_assets.py` which handles
  both `screenshot.svg` and `screenshot-score.svg`; `nox -s screenshot` updated
  to call the unified script.

- **`validate_links_async`** now uses a two-phase model:
  1. **Phase 1 (parallel index):** workers extract per-file anchors and
     resolved links.
  2. **Phase 2 (global validation):** main process validates links against the
     merged global anchor index.

- Architecture docs (`docs/architecture.md`, `docs/it/architecture.md`) Mermaid
  diagrams now explicitly show worker phases:
  - `Phase 1: Anchor Extraction (Parallel)`
  - `Phase 2: Rule Execution & Validation (Parallel)`

- Plugin SDK docs expanded with "zero to plugin in 30 seconds" fast-track in
  `docs/developers/plugins.md` and `docs/it/developers/plugins.md`.

- Plugin scaffold now imports from `zenzic.rules` (public namespace) instead of
  `zenzic.core.rules` (internal) (#13).

- Checks docs updated with Z001/Z002 violation code table in EN/IT (#6).

- Custom Rules DSL IT docs completed with Performance and Pattern tips (#4).

- CLI command references updated in EN/IT with `zenzic init --plugin` usage.

- `docs/usage/advanced.md` — new "Single-file and directory target" section
  documenting `PATH` argument syntax, adapter auto-selection, and use cases
  (pre-commit hooks, README review, Hugo `content/` dirs).

### Fixed

- **mypy errors** — `list[object]` annotations on `security_line` and
  `renderables` changed to `list[RenderableType]` (imported from
  `rich.console`); `config.docs_dir` (type `Path`) wrapped with `str()` when
  passed to `SentinelReporter(docs_dir=...)` which expects `str`.
  `mypy src/` — 0 errors in 30 files.

- **Exit-code under target mode** — `has_failures` now uses filtered findings
  (`errors > 0`) rather than `results.failed` (which counted off-target findings
  such as `zenzic.toml` classified as an unused asset when `docs_dir` was patched
  to `.`).  `test_check_all_no_strict_passes_on_warnings_only` continues to pass
  confirming that warning-only results exit 0 in non-strict mode.

- **Unused `# type: ignore[assignment]`** — stale comment at `cli.py:644` removed
  after mypy no longer required it following the `_apply_target` refactor.

### Tests

- `test_validator.py` updated: added `_ul()` helper to unwrap `LinkInfo` →
  `(url, lineno)` tuples; 13 assertion patterns updated for `LinkInfo`
  compatibility; 4 destructuring patterns migrated from `for u, _ in` to
  `for link in` with `.url` attribute access.
- 4 new CLI integration tests for target mode:
  `test_check_all_target_not_found`, `test_check_all_target_single_file`,
  `test_check_all_target_file_outside_docs`, `test_check_all_target_directory`.
- Test fixtures write ≥ 60-word bodies to avoid `short-content` placeholder warnings.

#### Mutation Testing Campaign — "The Mutant War"

- **Mutation score: 86.7%** (242/279 mutants killed on `rules.py`) — up from
  58.1% at baseline.  Target was 75%; exceeded by +11.7 pp.
- **80 new mutant-killing tests** added to `test_rules.py`, organised in
  dedicated test classes:
  - `TestExtractInlineLinksWithLines` (14 tests) — edge cases for inline link
    extraction including empty hrefs, escaped brackets, and multi-link lines.
  - `TestVSMBrokenLinkRuleMutantKill` (22 tests) — `check_vsm` path/anchor
    resolution logic, orphan detection, severity mapping, and `continue`/`break`
    branch coverage.
  - `TestAdaptiveRuleEngineRunMutantKill` (4 tests) — `AdaptiveRuleEngine.run()`
    short-circuit and content propagation.
  - `TestAdaptiveRuleEngineRunVsmMutantKill` (6 tests) — `run_vsm()` VSM-specific
    finding collection and file iteration.
  - `TestAssertPickleableMutantKill` (2 tests) — `assert_pickleable()` deep-copy
    and `UNREACHABLE` assertion guard.
  - `TestPluginRegistryMutantKill` (27 tests) — `PluginRegistry` discovery,
    duplicate handling, case-sensitivity, and `validate_rule()` contract.
  - `TestExtractLinksDeepMutantKill` (5 tests) — fence-block skipping, reference
    link parsing, and empty-document edge cases.
- **37 surviving mutants** classified as equivalent (no observable behaviour
  change) or framework limitations (unreachable defensive assertions).
- **Hypothesis property-based testing** integrated with three profiles:
  `dev` (50 examples), `ci` (500), `purity` (1 000).
- **mutmut 3.5.0** configured under `[tool.mutmut]` in `pyproject.toml`;
  runner: `python3 -m pytest -x`, target: `src/zenzic/core/rules.py`.
- **Performance baseline** relaxed from 150 ms → 200 ms for 5 000 in-memory
  resolutions to accommodate CI/nox environmental variance (resolver is O(1)).
- **706 tests pass.** `just preflight` — all gates green:
  ruff ✓ · mypy ✓ · pytest 80%+ coverage ✓ · REUSE ✓ · zenzic self-audit ✓ · mkdocs build --strict ✓.

## [0.5.0a2] — 2026-04-03 — The Refined Sentinel: Lean Package & Unified Workflow

> **Sprint 12.** Consolidation and DX hardening. Removes the `[docs]` public
> extra (engine-agnostic: users install MkDocs independently), eliminates
> `RELEASE.it.md` in favour of a single English source of truth, and unifies
> the developer workflow under `just`. `bump-my-version` gains a PEP 440
> pre-release parser/serializer so `pre_n` bumps work correctly.

### Removed

- `[project.optional-dependencies]` — `zenzic[docs]` extra eliminated; MkDocs
  is a user-managed dependency, not a package extra
- `RELEASE.it.md` — release notes consolidated to `RELEASE.md` (English only)
- Hardcoded-date `bumpversion` patterns for `RELEASE.md`, `CITATION.cff`, and
  `docs/community/index.md`; dates updated manually at release time

### Changed

- `justfile`: `zensical build/serve` replaced with `mkdocs build --strict` /
  `mkdocs serve`; added `just check` (self-linting duty); `clean` now removes
  `dist/` and `.zenzic-score.json`
- `CONTRIBUTING.md`: Quick Start updated to `just sync`; task table aligned to
  current `just` commands
- `docs/developers/index.md`: added *Interactive Workflow with Just* section
- All `zenzic[docs]` references replaced with *Lean & Agnostic by Design*
  narrative across `README.md`, `README.it.md`, `docs/usage/index.md`,
  `docs/it/usage/index.md`, and contributor guides
- `pyproject.toml` `[tool.bumpversion]`: added `parse`, `serialize`, and
  `parts.pre_n` for PEP 440 pre-release support; removed `mkdocs.yml` entry
  (version is injected via `!ENV`, not a literal string)
- `CITATION.cff`, `docs/community/index.md`, `docs/it/community/index.md`:
  aligned to `0.5.0a2`

---

## [0.5.0a1] — 2026-04-02 — The Sentinel: Hybrid Adaptive Engine & Plugin System

> **Sprint 11.** Zenzic enters the v0.5 cycle with a unified execution model and a
> first-class plugin system.  `scan_docs_references` replaces the two separate serial
> and parallel functions.  The engine selects sequential or `ProcessPoolExecutor` mode
> automatically based on repository size (threshold: 50 files).  All rules are validated
> for pickle-serializability at construction time.  Core rules are now registered as
> entry-points under `zenzic.rules`, establishing the public plugin contract.

### BREAKING CHANGES

- **`scan_docs_references` signature changed.**  The function now returns
  `tuple[list[IntegrityReport], list[str]]` instead of `list[IntegrityReport]`.
  Callers that ignored link errors must unpack the tuple:

  ```python
  # Before (0.4.x)
  reports = scan_docs_references(repo_root)

  # After (0.5.x)
  reports, _ = scan_docs_references(repo_root)
  ```

- **`scan_docs_references_parallel` and `scan_docs_references_with_links` are
  removed.**  Use `scan_docs_references(..., workers=N)` and
  `scan_docs_references(..., validate_links=True)` respectively.

- **`RuleEngine` is removed.**  The class is now `AdaptiveRuleEngine` with no
  alias.  The constructor runs eager pickle validation on every rule and raises
  `PluginContractError` if any rule is not serialisable.

### Added

- **`AdaptiveRuleEngine`** (`zenzic.core.rules`) — unified rule engine with
  Hybrid Adaptive Mode.  Replaces and removes `RuleEngine` (no alias).
  Validates all rules for pickle-serializability at construction time via
  `_assert_pickleable()`.

- **`_assert_pickleable(rule)`** (`zenzic.core.rules`) — module-level helper
  called by `AdaptiveRuleEngine.__init__`.  Raises `PluginContractError` on
  failure with a diagnostic message including the rule ID, class name, and the
  pickle error.

- **`ADAPTIVE_PARALLEL_THRESHOLD`** (`zenzic.core.scanner`) — module-level
  constant (default: `50`).  The file count above which parallel mode activates.
  Exposed for test overrides without patching private internals.

- **`PluginContractError`** (`zenzic.core.exceptions`) — new exception for rule
  plugin violations.  Added to the exception hierarchy docstring.

- **`zenzic.rules` entry-point group** (`pyproject.toml`) — core rules
  registered as first-class plugins:

  ```toml
  [project.entry-points."zenzic.rules"]
  broken-links = "zenzic.core.rules:VSMBrokenLinkRule"
  ```

- **`docs/developers/plugins.md`** (EN + IT) — new page documenting the rule
  plugin contract: module-level requirement, pickle safety, purity, packaging
  via `entry_points`, `plugins` key in `zenzic.toml`, error isolation, and a
  pre-publication checklist.

- **`docs/developers/index.md`** (EN + IT) — added link to `plugins.md`.

- **`zenzic plugins list`** — new CLI sub-command.  Lists every rule registered
  in the `zenzic.rules` entry-point group with its `rule_id`, origin
  distribution, and fully-qualified class name.  Core rules are labelled
  `(core)`; third-party rules show the installing package name.

- **`pyproject.toml` configuration support (ISSUE #5)** — `ZenzicConfig.load()`
  now follows a three-level Agnostic Citizen priority chain:
  `zenzic.toml` (Priority 1) → `[tool.zenzic]` in `pyproject.toml`
  (Priority 2) → built-in defaults (Priority 3).  If both files exist,
  `zenzic.toml` wins unconditionally.

- **`plugins` config key** (`zenzic.toml` / `[tool.zenzic]`) —
  `ZenzicConfig.plugins` now exposes an explicit allow-list of external
  rule plugin entry-point names to activate during scanning.  Core rules
  remain always enabled.

- **`scan_docs_references` `verbose` flag** — new keyword-only parameter
  `verbose: bool = False`.  When `True`, prints a one-line performance
  telemetry summary to stderr after the scan: engine mode (Sequential or
  Parallel), worker count, file count, elapsed time, and estimated speedup
  (parallel mode only).

- **`PluginRuleInfo` dataclass** (`zenzic.core.rules`) — lightweight struct
  returned by the new `list_plugin_rules()` discovery function.  Fields:
  `rule_id`, `class_name`, `source`, `origin`.

- **`docs/configuration/index.md`** (EN + IT) — "Configuration loading" section
  expanded with the three-level priority table and a `[tool.zenzic]` example.

### Changed

- **`scan_docs_references`** (`zenzic.core.scanner`) — unified function
  replacing `scan_docs_references` + `scan_docs_references_parallel`.  New
  signature:

  ```python
  scan_docs_references(
      repo_root, config=None,
      *, validate_links=False, workers=1
  ) -> tuple[list[IntegrityReport], list[str]]
  ```

  Hybrid Adaptive Mode: sequential when `workers=1` or `< 50 files`; parallel
  (`ProcessPoolExecutor`) otherwise.  Results always sorted by `file_path`.

- **`docs/architecture.md`** and **`docs/it/architecture.md`** — "Parallel scan
  (v0.4.0-rc5)" section replaced by "Hybrid Adaptive Engine (v0.5.0a1)" with
  a Fan-out/Fan-in Mermaid diagram showing the threshold decision node.
  IT section was previously absent; added from scratch.

- **`docs/usage/advanced.md`** and **`docs/it/usage/advanced.md`** — parallel
  scan section rewritten to document the unified `scan_docs_references` API and
  the Hybrid Adaptive Engine threshold table.

- **`docs/usage/commands.md`** (EN + IT) — added `zenzic plugins list` command
  documentation and `--workers` flag reference for the Hybrid Adaptive Engine.

- **`README.md`** — "RC5 Highlights" replaced by "v0.5.0a1 Highlights —
  The Sentinel".

- **`pyproject.toml`** — version bumped to `0.5.0a1`.

- **`src/zenzic/__init__.py`** — `__version__` bumped to `"0.5.0a1"`.

### Removed

- `scan_docs_references_parallel` — deleted; use `scan_docs_references(..., workers=N)`.
- `scan_docs_references_with_links` — deleted; use `scan_docs_references(..., validate_links=True)`.
- `RuleEngine` — deleted; use `AdaptiveRuleEngine` directly.

---

## 0.4.x (abandoned)

This release cycle was exploratory and included multiple breaking changes.
It has been superseded by the 0.5.x stabilization cycle.

## [0.4.0-rc4] — 2026-04-01 — Ghost Route Support, VSM Rule Engine & Content-Addressable Cache

## [0.4.0-rc5] — 2026-04-01 — The Sync Sprint: Zensical v0.0.31+ & Parallel API

> **Sprint 10.** `ZensicalAdapter` is fully synchronised with Zensical v0.0.31+.
> The legacy `[site]`/`[nav].nav` schema is replaced by the canonical `[project].nav`
> format.  Navigation parsing now supports all three entry forms (plain string, titled page,
> nested section) recursively.  `classify_route()` gains nav-aware orphan detection.
> `map_url()` honours `use_directory_urls = false`.  The parallel scan API is stabilised
> and documented with explicit pickling requirements for custom rules.
> `examples/zensical-basic/` is introduced as the canonical Zensical reference project.
> All Zensical TOML snippets in `docs/` are updated to the v0.0.31+ schema.

### Added

- **`examples/zensical-basic/`** — new canonical example project for `engine = "zensical"`.
  Contains a `zensical.toml` using `[project].nav` with all three nav entry forms, a
  `zenzic.toml` with `engine = "zensical"`, and a complete `docs/` tree with clean
  relative links.  `zenzic check all` on this example exits 0.

- **`_extract_nav_paths()`** (`zenzic.core.adapters._zensical`) — new pure helper that
  recursively extracts `.md` file paths from a Zensical nav list.  Handles plain strings
  (`"page.md"`), titled pages (`{"Title" = "page.md"}`), and nested sections
  (`{"Section" = [...]}`).  External URLs are silently skipped.

- **Nav-aware `classify_route()`** — when an explicit `[project].nav` is declared in
  `zensical.toml`, files absent from the nav list are now classified
  `ORPHAN_BUT_EXISTING` instead of `REACHABLE`.  Zensical serves every file (filesystem
  routing), but the sidebar is the user-visible navigation: files outside the nav are
  effectively invisible.

- **`use_directory_urls` support** in `ZensicalAdapter.map_url()` — reads
  `[project].use_directory_urls` from `zensical.toml`.  When `false`, files are mapped
  to flat `.html` URLs (`/page.html`) instead of directory URLs (`/page/`).  Default
  remains `true`, matching Zensical's own default.

- **Parallelism section in `docs/usage/advanced.md`** — documents
  `scan_docs_references_parallel`, the performance crossover point (~200 files),
  the absence of a `--parallel` CLI flag in rc5, and the **pickling requirements** for
  custom `BaseRule` subclasses.

- **Parallelism section in `docs/architecture.md`** — describes the shared-nothing
  `ProcessPoolExecutor` model, the immutability contract on workers, and the performance
  threshold with honest numbers.

- **Engine coexistence section in `docs/configuration/adapters-config.md`** (EN + IT) —
  documents behaviour when both `mkdocs.yml` and `zensical.toml` are present.  Clarifies
  that `build_context.engine` is always authoritative; no auto-detection occurs.

- **`ZensicalAdapter` nav format reference in `docs/configuration/adapters-config.md`**
  (EN + IT) — full TOML examples of all three nav entry forms, route classification rules
  with and without explicit nav, and `use_directory_urls` documentation.

### Changed

- **`ZensicalAdapter.__init__`** — pre-computes `_nav_paths`, `_has_explicit_nav`, and
  `_use_directory_urls` at construction time from `[project]` in `zensical.toml`.
  `get_nav_paths()` is now an O(1) attribute read.

- **`ZensicalAdapter` docstring** — updated from legacy `[nav].nav = [{title, file}]`
  schema to the v0.0.31+ `[project].nav = [...]` format.

- **`tests/sandboxes/zensical/zensical.toml`** — migrated from flat key schema to
  `[project]` scope.  Added a three-entry `nav` list (`index.md`, `features.md`,
  `api.md`) to exercise orphan detection in integration tests.

- **`docs/guide/migration.md`** and **`docs/it/guide/migration.md`** — Phase 3 example
  `zensical.toml` updated from legacy `[site]`/`[nav].nav` to `[project].nav` format.

### Fixed

- **`ZensicalAdapter.get_nav_paths()`** previously read `[nav].nav` using `{title, file}`
  key format — a schema that was never part of the official Zensical spec.  Fixed to read
  `[project].nav` using the actual v0.0.31+ format.

- **`ZensicalAdapter.classify_route()`** previously returned `REACHABLE` for all
  non-private files regardless of nav declaration.  Fixed to return `ORPHAN_BUT_EXISTING`
  when an explicit nav is declared and the file is absent from it.

---

## [0.4.0-rc4] — 2026-04-01 — Ghost Route Support, VSM Rule Engine & Content-Addressable Cache
>
> **Sprint 9.** The Virtual Site Map (VSM) becomes the single source of truth for the Rule
> Engine.  MkDocs Material Ghost Routes are resolved without false orphan warnings.
> The `VSMBrokenLinkRule` validates links against routing state rather than the filesystem.
> A content-addressable cache eliminates redundant re-linting of unchanged files.
> The `Violation` dataclass introduces a structured finding standard with `code`, `level`,
> and `context` fields.  `RuleFinding` is scheduled for removal before final release.

### Added

- **Ghost Route support** (`MkDocsAdapter`) — when `mkdocs.yml` declares
  `plugins.i18n.reconfigure_material: true`, the Material theme auto-generates locale
  entry points (e.g. `it/index.md` → `/it/`) at build time.  These pages are never listed
  in `nav:` but are live routes.  `classify_route()` now marks top-level locale index files
  as `REACHABLE` when this flag is set, eliminating false `ORPHAN_BUT_EXISTING` findings.
  Guarded to `docs_structure: folder` only; suffix mode is unaffected.

- **Redundant config warning** — `MkDocsAdapter.__init__` emits a `logging.WARNING` when
  both `reconfigure_material: true` and `extra.alternate` are present in `mkdocs.yml`.
  The combination suppresses the language switcher in some plugin versions.  The warning
  names the exact key to remove.  Detection via the new pure helper
  `_detect_redundant_alternate()`.

- **`Violation` dataclass** (`zenzic.core.rules`) — structured finding type for VSM-aware
  rules.  Fields: `code` (e.g. `Z001`), `level` (`error`/`warning`/`info`), `context`
  (raw source line).  `as_finding()` converts to `RuleFinding` for backwards compatibility
  during the transition period.

- **`BaseRule.check_vsm()`** — new optional method on `BaseRule`.  Receives
  `(file_path, text, vsm, anchors_cache)` — all in-memory, no I/O.  Default no-op
  preserves full backwards compatibility for existing `check()`-only subclasses.

- **`RuleEngine.run_vsm()`** — companion to `run()`.  Calls `check_vsm` on every rule,
  converts `Violation` objects to `RuleFinding`, and isolates exceptions identically to
  `run()`.

- **`VSMBrokenLinkRule`** (code `Z001`) — first VSM-aware built-in rule.  Validates every
  inline Markdown link against `vsm[url].status`.  A link is valid only when its target
  URL is `REACHABLE` in the VSM — meaning Ghost Routes, nav-listed pages, and locale
  shadows all pass cleanly.  Orphan and ignored pages emit `UNREACHABLE_LINK`.  External
  URLs and bare fragments are skipped.  `check()` is a documented no-op.

- **`CacheManager`** (`zenzic.core.cache`) — content-addressable in-memory cache for rule
  findings.  Key: `SHA256(content) + SHA256(config) [+ SHA256(vsm_snapshot)]`.
  - *Atomic rules* (e.g. `CustomRule`): key omits VSM hash; cache survives unrelated file
    changes.
  - *Global rules* (e.g. `VSMBrokenLinkRule`): key includes VSM hash; entire routing-state
    change invalidates entries.
  - Persistence: `load()` / `save()` are the only I/O operations; `get()` / `put()` are
    pure in-memory.  Atomic write via temp-file rename prevents corruption.
  - Degrades silently to cold start on missing or corrupt cache file.

- **`make_vsm_snapshot_hash()`** — pure function that produces a stable SHA-256 digest of
  VSM routing state (url, source, status, anchors).  Deterministic: routes sorted by URL,
  anchor sets sorted before serialisation.

- **Rule dependency taxonomy** — documented in `rules.py` module docstring:
  *Atomic* (single-file, cache key omits VSM), *Global* (VSM-aware, cache key includes VSM
  snapshot), *Cross-file* (future; not cacheable per-file without a dependency graph).

### Changed

- **`classify_route()` docstring** — enumeration extended to rule 3 (Ghost Route) and rule
  4 (ORPHAN fallback) with explicit note that rules fire in priority order and an explicit
  nav entry always wins.

- **README `## First-Class Integrations`** — new "How it works — Virtual Site Map (VSM)"
  subsection explains the VSM pipeline, Ghost Routes, and content-addressable cache.

### Fixed

- **`extra.alternate` + `reconfigure_material` conflict** (`mkdocs.yml`) — removed the
  redundant `extra.alternate` block from the project's own `mkdocs.yml`.  This was causing
  the language switcher to disappear in `mkdocs-material` when `reconfigure_material: true`
  is active.

### Developer Guide

- **`docs/guide/migration.md`** and **`docs/it/guide/migration.md`** — new
  "MkDocs Material best practices / Language switcher optimisation" section explains the
  `reconfigure_material` vs `extra.alternate` conflict and provides the recommended
  configuration pattern.

### Tests

- `TestGhostRouteReconfigureMaterial` (9 tests) — Ghost Route invariants: positive path
  (`reconfigure_material: true` → `REACHABLE`), regression path (flag off/absent →
  `ORPHAN_BUT_EXISTING` for non-shadow pages), boundary (explicit nav entry not overridden,
  nested locale pages not promoted), end-to-end VSM integration.
- `TestViolation` — `Violation` contract: fields, `is_error`, `as_finding()` round-trip.
- `TestVSMBrokenLinkRule` — 11 tests covering REACHABLE pass, missing URL, orphan status,
  external skip, fragment skip, fenced-block skip, context/line-number correctness,
  `run_vsm` engine integration.
- `TestRuleEngineTortureTest` — O(N) scalability: 10 000-node VSM + 10 000 links completes
  in < 1 s for both all-valid and all-missing cases.

---

## [0.4.0-rc3] — 2026-03-31 — Virtual Site Map, UNREACHABLE_LINK & Routing Collision Detection

> **Sprint 8.** Zenzic gains build-engine emulation: the Virtual Site Map (VSM) projects
> every source file to its canonical URL before the build runs.  Links to pages that exist
> on disk but are absent from the nav are now caught as `UNREACHABLE_LINK`.  Routing
> collisions (e.g. `index.md` + `README.md` coexisting in the same directory) are flagged
> as `CONFLICT`.  Documentation paths unified under `/guide/`.  Terminology aligned to
> "compatible successor".

### Added

- **Virtual Site Map (VSM)** — new `zenzic.models.vsm` module introduces the `Route`
  dataclass (`url`, `source`, `status`, `anchors`, `aliases`) and `build_vsm()`, a
  zero-I/O function that projects every `.md` source file to its canonical URL and
  routing status (`REACHABLE`, `ORPHAN_BUT_EXISTING`, `IGNORED`, `CONFLICT`) using
  the active build-engine adapter.  Zenzic now emulates the site router without running
  the build.

- **`UNREACHABLE_LINK` detection** — `validate_links_async` now cross-references every
  successfully resolved internal link against the VSM.  A link to a file that exists on
  disk but is not listed in the MkDocs `nav:` emits `UNREACHABLE_LINK`, catching the
  class of 404s that traditional file-existence checks miss entirely.  Disabled
  automatically for `VanillaAdapter` and `ZensicalAdapter` (filesystem-only routing).

- **Routing collision detection** — `_detect_collisions()` in `vsm.py` marks any two
  source files that map to the same canonical URL as `CONFLICT`.  The most common case
  — `index.md` and `README.md` coexisting in the same directory (Double Index) — is
  handled without special-casing: both produce the same URL and are therefore caught
  automatically.

- **`map_url()` and `classify_route()` adapter methods** — added to `BaseAdapter`
  Protocol, `MkDocsAdapter`, `ZensicalAdapter`, and `VanillaAdapter`.  `map_url(rel)`
  applies engine-specific physical → virtual URL mapping; `classify_route(rel, nav_paths)`
  returns the routing status for a given source file.

### Changed

- **`MkDocsAdapter.classify_route`** — when no `nav:` section is declared in
  `mkdocs.yml`, all files are classified as `REACHABLE` (mirrors MkDocs auto-include
  behaviour).  `README.md` remains `IGNORED` regardless.

- **Documentation paths** — all references to the stale `/guides/` path in `RELEASE.md`,
  `RELEASE.it.md`, `CHANGELOG.md`, `CHANGELOG.it.md`, and `README.it.md` updated to
  the canonical `/guide/` root.

### Fixed

- **Terminology** — "Zensical is a superset of MkDocs" replaced with "Zensical is a
  compatible successor to MkDocs" across all documentation and changelog entries.

---

## [0.4.0-rc3] — 2026-03-29 — i18n Anchor Fix, Multi-language Snippets & Shield Deep-Scan

> **Sprint 7.** The `AnchorMissing` i18n fallback gap closed. Dead code eliminated. Shared
> locale path-remapping utility extracted. Visual Snippets for custom rule findings. Usage docs
> split into three focused pages. JSON schema stabilised at 7 keys. Multi-language snippet
> validation (Python/YAML/JSON/TOML) and full-file Shield deep-scan added.

### Added

- **Multi-language snippet validation** — `check_snippet_content` now validates fenced code
  blocks for four languages using pure Python parsers (no subprocesses):
  `python`/`py` → `compile()`; `yaml`/`yml` → `yaml.safe_load()`; `json` → `json.loads()`;
  `toml` → `tomllib.loads()`. Blocks with unsupported language tags (e.g. `bash`) are silently
  skipped. `_extract_python_blocks` renamed to `_extract_code_blocks` to reflect the broader
  scope.

- **Shield deep-scan — credentials in fenced blocks** — The credential scanner now operates on
  every line of the source file, including lines inside fenced code blocks (labelled or
  unlabelled). Previously, `_iter_content_lines` fed both the Shield and the reference harvester,
  causing fenced content to be invisible to the Shield. A new `_skip_frontmatter` generator
  provides a raw line stream (minus frontmatter only); `harvest()` now runs two independent
  passes — Shield on the raw stream, ref-defs + alt-text on the filtered content stream. Links
  and reference definitions inside fenced blocks remain ignored to prevent false positives.

- **Shield extended to 7 credential families** — Added Stripe live keys
  (`sk_live_[0-9a-zA-Z]{24}`), Slack tokens (`xox[baprs]-[0-9a-zA-Z]{10,48}`), Google API
  keys (`AIza[0-9A-Za-z\-_]{35}`), and generic PEM private keys
  (`-----BEGIN [A-Z ]+ PRIVATE KEY-----`) to `_SECRETS` in `core/shield.py`.

- **`resolve_anchor()` method on `BaseAdapter` protocol** — New adapter method that returns
  `True` when an anchor miss on a locale file should be suppressed because the anchor exists
  in the default-locale equivalent. Implemented in `MkDocsAdapter`, `ZensicalAdapter` (via
  `remap_to_default_locale()`), and `VanillaAdapter` (always returns `False`).

- **`adapters/_utils.py` — `remap_to_default_locale()` pure utility** — Extracts the shared
  locale path-remapping logic that was independently duplicated across `resolve_asset()` and
  `is_shadow_of_nav_page()` in both adapters. Pure function: takes `(abs_path, docs_root,
  locale_dirs)`, returns the default-locale equivalent `Path` or `None`. Zero I/O.

- **Visual Snippets for `[[custom_rules]]` findings** — Custom rule violations now display the
  offending source line below the finding header, prefixed with the `│` indicator rendered in
  the finding's severity colour. Standard check findings are unaffected.

- **`strict` and `exit_zero` as `zenzic.toml` fields** — Both flags are now first-class
  `ZenzicConfig` fields (type `bool | None`, sentinel `None` = not set). CLI flags override
  TOML values. Enables project-level defaults without CLI ceremony.

- **JSON output schema — 7 stable keys** — `--format json` emits:
  `links`, `orphans`, `snippets`, `placeholders`, `unused_assets`, `references`, `nav_contract`.

- **Usage docs split** — `docs/usage/index.md` split into three focused pages:
  `usage/index.md` (install + workflow), `usage/commands.md` (CLI reference),
  `usage/advanced.md` (three-pass pipeline, Shield, programmatic API, multi-language).
  Italian mirrors (`docs/it/usage/`) at full parity. `mkdocs.yml` nav updated.

### Fixed

- **`AnchorMissing` had no i18n fallback suppression** — The `AnchorMissing` branch in
  `validate_links_async` reported unconditionally. Links to translated headings in locale files
  generated false positives. Fix: `AnchorMissing` branch now calls `adapter.resolve_anchor()`.
  Five new integration tests in `TestI18nFallbackIntegration` cover: suppressed miss, miss in
  both locales, fallback disabled, EN source file, direct resolution.

### Removed

- **`_should_suppress_via_i18n_fallback()`** — Dead code. Was defined in `validator.py` but
  never called. Removed permanently.
- **`I18nFallbackConfig` NamedTuple** — Internal data structure for the above deleted function.
  Removed.
- **`_I18N_FALLBACK_DISABLED` sentinel** — Constant for the above deleted function. Removed.
- **`_extract_i18n_fallback_config()`** — Also dead. Was tested by `TestI18nFallbackConfig`
  (6 tests), which is also removed. Total removal: ~118 lines from `validator.py`.

### Tests

- 5 new anchor fallback integration tests in `TestI18nFallbackIntegration`.
- `TestI18nFallbackConfig` (6 tests for deleted functions) removed.
- 8 new snippet validation tests (YAML valid/invalid, `yml` alias, JSON valid/invalid,
  JSON line-number accuracy, TOML valid/invalid).
- 5 new Shield deep-scan tests: secret in unlabelled fence, secret in `bash` fence,
  secret in fence with no ref-def created, clean code block no findings, combined invariant.
- **446 tests pass.** `nox preflight` — all gates green: ruff ✓ mypy ✓ pytest ✓ reuse ✓
  mkdocs build --strict ✓ zenzic check all --strict ✓.

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
  `it/guide/migration.md`.

- **Documentation — Writing an Adapter guide** (`docs/developers/writing-an-adapter.md`) —
  Full protocol reference: `BaseAdapter` methods, `from_repo` pattern, entry-point
  registration, test utilities (`RepoBuilder`, `assert_no_findings`, protocol compliance
  checker).

- **Documentation — MkDocs → Zensical migration guide** (`docs/guide/migration.md`) —
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

- `_detect_engine()` — `--engine` override now validates both binary presence on `$PATH` and required config file existence before returning; `--engine zensical` accepts `mkdocs.yml` as a valid config for backwards compatibility (Zensical is a compatible successor to MkDocs); returns `None` when no config file is present, enabling the static-server fallback instead of raising an error.

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

[Unreleased]:       https://github.com/PythonWoods/zenzic/compare/v0.6.0a2...HEAD
[0.6.0a2]:          https://github.com/PythonWoods/zenzic/compare/v0.6.0a1...v0.6.0a2
[0.6.0a1]:          https://github.com/PythonWoods/zenzic/compare/v0.5.0a3...v0.6.0a1
[0.5.0a5]:          https://github.com/PythonWoods/zenzic/compare/v0.5.0a2...v0.5.0a3
[0.5.0a2]:          https://github.com/PythonWoods/zenzic/compare/v0.5.0a1...v0.5.0a2
[0.5.0a1]:          https://github.com/PythonWoods/zenzic/compare/v0.4.0-rc5...v0.5.0a1
[0.4.0-rc5]:        https://github.com/PythonWoods/zenzic/compare/v0.4.0-rc4...v0.4.0-rc5
[0.4.0-rc4]:        https://github.com/PythonWoods/zenzic/compare/v0.4.0-rc3...v0.4.0-rc4
[0.4.0-rc3]:        https://github.com/PythonWoods/zenzic/compare/v0.4.0-rc2...v0.4.0-rc3
[0.4.0-rc2]:        https://github.com/PythonWoods/zenzic/releases/tag/v0.4.0-rc2
