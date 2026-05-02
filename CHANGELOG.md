<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

> **Older versions (v0.1.0 – v0.5.x):** See the [Changelog Archive](CHANGELOG.archive.md).

## [0.7.0] — target release date 2026-05-05 — Quartz Maturity (Stable)

Zenzic v0.7.0 marks the transition to a **Sovereign Knowledge System**. After the Obsidian
Siege and the Quartz Tribunal, this release establishes the **Quartz standard** for precision,
security, and documentation integrity. The codebase achieves structural maturity: 1,342 tests,
80%+ coverage, dynamic SARIF sovereignty, engine auto-discovery, and a hardened Shield with
speculative Base64 decoding. Supersedes v0.6.1.

> **Legacy Documentation:** Versions prior to v0.7.0 are officially deprecated and do not follow
> the current Diátaxis architecture. For historical reference, see the
> [v0.6.1 GitHub Release](https://github.com/PythonWoods/zenzic/releases/tag/v0.6.1).
> The authoritative source is [zenzic.dev](https://zenzic.dev).

## [Unreleased]

### D097 — CLOSING PROTOCOL Enforcement (2026-05-01)

#### Added

- **CHANGELOG ordering invariant (CEO-293)** codified in `ZENZIC_BRAIN.md` [CLOSING PROTOCOL]
  Step 2. Newest sprint always inserted at TOP of `[Unreleased]`; each sprint is a `### Dxxx`
  heading; CEO groups are `#### CEO-nnn` sub-headings; `#### Tests` with count is mandatory
  and always the LAST sub-section of the sprint block.
- **`CONTRIBUTING.md` point 4:** CHANGELOG update mandatory in the same commit as the code
  change — not deferred to release day. Closes the structural gap that caused D096 to land
  incomplete across multiple commits.

#### Fixed

- **CHANGELOG.md / CHANGELOG.it.md D096 structure:** duplicate `#### Tests` section removed;
  `### D095` heading restored with correct `---` separator. Root cause: insertion used the
  `#### Tests` + `---` + heading as `oldString` context and consumed the separator.

#### CEO-298 — Parallel Fail-Fast

- **`scan_docs_references()` coordinator** replaced with `concurrent.futures.wait(FIRST_COMPLETED)` +
  local `_abort` flag. First `SecurityFinding` in any worker result cancels all still-queued
  (`PENDING`) futures; `RUNNING` workers complete and their results are silently discarded.
- **ZRT-002 deadlock guard** preserved: empty `done` set → Z009. `_worker()` and
  `_scan_single_file()` unchanged (Pillar 3).
- **ADR-020** added: Parallel Audit Completeness vs. Fail-Fast.
- **`tests/test_integration_finale.py`:** 3 new CEO-298 regression tests (fail-fast abort,
  ZRT-002 Z009 guard, sorted output invariant).

#### CEO-DX — CLI DX Refactoring (`brain map`)

- **Short flags:** `-c` alias for `--check`, `-f` alias for `--format`.
- **Smart Format Inference:** `output_format` changed to `str | None`; inferred from `--output`
  file extension when not provided (`.json` → `json`, `.md` → `markdown`; unknown extension →
  Exit 2 graceful).
- **Conflict detection:** `--format md` + `-o out.json` → Exit 2 with clear message
  (Fail Fast and Loud invariant).
- **Directory auto-creation:** `output.parent.mkdir(parents=True, exist_ok=True)` before
  `write_text` — no more `FileNotFoundError` on deep paths.
- **`tests/test_brain.py`:** 7 new `TestBrainMapDX` tests (91 total in module).

#### CEO-DX-Global — Global CLI DX Standardization

- **GAP-00:** `brain_map` path argument made required (`no_args_is_help=True` now effective;
  no silent CWD fallback).
- **GAP-01:** `-f` short alias added to `--format` in 8 commands (`check links`, `check orphans`,
  `check snippets`, `check references`, `check assets`, `check all`, `score`, `diff`).
- **GAP-02:** `init --plugin` conflict detection — `--plugin + --dev` or `--plugin + --pyproject`
  exits 2.
- **GAP-04:** `check all --strict + --exit-zero` mutual-exclusion guard (Exit 2).
- **GAP-06:** `RuntimeError`/`ConfigurationError` hardening in `check all`, `score`, `diff` —
  user-friendly Exit 1 with ERROR message.
- **~18 new regression tests** across `test_brain.py` (`TestBrainMapGAP00`) and `test_cli.py`
  (GAP-01 through GAP-06).

#### Tests

- **1,519 passed · ≥83% coverage** (Python 3.11 / 3.12 / 3.13). No regressions.

---

### D096 — Quartz Discovery, SARIF Sovereignty & Brain Curation (2026-04-30)

#### Added

- **`discover_engine(repo_root) -> str`** in `core/adapters/_factory.py`. `get_adapter()` resolves
  `engine="auto"` via `discover_engine()` before cache key lookup. Priority: `zensical.toml` →
  `docusaurus.config.ts/js` → `mkdocs.yml` → `"standalone"`.
- **`engine` default changed** from `"mkdocs"` to `"auto"` in `models/config.py`.
- **Z906 NO_FILES_FOUND** registered in `codes.py`. Note level, exit 0, text-only (Rule R20).
- **SARIF rules generated dynamically** from `codes.py` in `cli/_shared.py`. Ghost codes
  Z301/Z601/Z701 eliminated. `helpUri` per rule: `https://zenzic.dev/docs/reference/finding-codes#{code.lower()}`.
- **`ZenzicExitCode` class** in `codes.py`: `SUCCESS=0`, `QUALITY=1`, `SHIELD=2`, `SENTINEL=3`.
- **`zenzic init` Quartz Template**: `_detect_init_engine()` delegates to `discover_engine()`.
  Generated `zenzic.toml` sets `fail_under = 100` and `strict = true` as active defaults.
- **Trinity Mesh Awareness** in `scripts/map_project.py`: Zone B auditor (`<!-- ZONE_B_START -->`
  / `<!-- ZONE_B_END -->` markers, 400-line guardrail, `[Z907] MEMORY_OVERFLOW` warning) +
  sibling repo detection (`[MESH STATUS]` block).
- **Zone A/B restructure** applied to all 3 public `ZENZIC_BRAIN.md` files (core, doc, action).
  Zone A = Constitutional (Manifesto, Policies, ADRs). Zone B = Operational ([ACTIVE SPRINT]).
- **"The Zenzic Memory Contract"** section added to `CONTRIBUTING.md` (CEO-237).
- **Contemporary Testimony** (zenzic-doc): Z906 in `finding-codes.mdx` EN+IT; engine `"auto"`
  in `configuration-reference.mdx` EN+IT; blog updated to 20 Acts + Act 19 row.
- **ADR-015** (SARIF Sovereign Automation) and **ADR-016** (Quartz Auto-Discovery) added to
  `ZENZIC_BRAIN.md`.

#### Sovereign Cartography & Identity Gate (CEO-242–249)

- **`src/zenzic/core/cartography.py`** — pure AST scanner: `scan_python_sources`,
  `render_markdown_table`, `update_ledger`. Zero subprocesses (Pillar 2).
- **`src/zenzic/cli/_brain.py`** — `brain` sub-app (`map` command): Zone B auditor,
  Trinity Mesh probe, Master-Shadow Sync. Gated by PEP 610 Identity Gate (`_is_dev_mode()`).
  End-users cannot discover the command group.
- **`just brain-map`** wired into `verify` / `preflight`. R24 Zero-Amnesia Law.
- **ADR-017** (Sovereign Cartography & Identity Gate) added to `ZENZIC_BRAIN.md`.
- **CEO-249 Canary Hardening:** `_CANARY_STRINGS` lengths n=30→50 / n=25→40 / n=20→32,
  guaranteeing O(2^50) backtracking paths. `_CANARY_TIMEOUT_S` 0.1→0.05.
  Test pattern `(a|aa)+` → `(a+)+` — ADR-018 documents the SIGALRM rationale.

#### Quartz Audit Gate (CEO-257–258)

- **`zenzic brain map --check`** — read-only audit mode. Exits 1 with `D001 MEMORY_STALE`
  if [CODE MAP] is out of sync with `src/`. Pre-commit hook `brain-map-check` added.

#### Developer Integrity Seal + Environmental Privacy Gate (CEO-259–283)

- **`cartography.py`** extended: `load_dev_gate()`, `check_perimeter()` (literal, no regex,
  ReDoS-safe), `check_sources_perimeter()`, `redact_perimeter()` (Sovereign Redactor),
  `render_json()` (machine-readable AST). ADR-019.
- **D002 dual-spectrum gate:** Phase A = Sovereign Redactor (silent `[REDACTED_BY_SENTINEL]`).
  Phase B = VCS-Aware source audit (`walk_files + LayeredExclusionManager`, `.py/.md/.mdx/.toml/.yml`).
  Sovereign Immunity: `.zenzic.dev.toml` always immune via `exclude=frozenset({dev_toml.resolve()})`.
- **Synthetic Test Protocol (CEO-279):** forbidden token never on disk — assembled at runtime
  from `_PART_A` / `_PART_B` fragments. Zero D002 Phase B self-violation.
- **Lean Perimeter Standard (CEO-280):** `forbidden_patterns` trimmed to 1 entry across all repos.
- **Unified Vision Sweep (CEO-283):** `scan_python_sources` migrated from `rglob` to
  `walk_files + LayeredExclusionManager`. Zero `rglob` in any production module.

#### Environmental Sovereignty (CEO-252)

- **`--no-external`** flag added to `check links` and `check all` (CEO-056 CLI Symmetry).
  Skips Pass 3 (HTTP HEAD requests) independently of `--strict`. Shield (Z201/Z202/Z203) always
  fires — it operates on raw file content, not network. INFO transparency message in text mode
  (Rule R20 compliant). Pre-commit dev hook updated to `--strict --no-external` for offline gate.
- **`check_external: bool = True`** param propagated through `validate_links_async()`,
  `validate_links()`, `validate_links_structured()`, `_collect_all_results()`.
- **R27 Environmental Sovereignty** codified in `ZENZIC_BRAIN.md` [POLICIES].
- **`cli.mdx` EN+IT** updated: `--no-external` flag tables (zenzic-doc).

#### Tests

- **1,452 passed · ≥83% coverage** (Python 3.11 / 3.12 / 3.13). No regressions.
  `test_brain.py`: 84 tests. `test_validator.py::TestCheckExternalFlag`: 3 new tests.
  `test_cli.py`: existing signature test updated for `check_external=True`.

---

### D095 — The Base64 Sentinel Decoder & Universal Path Invariant

#### Added

- **Base64 speculative decoder in `shield.py` (CEO-194).** `_BASE64_CANDIDATE_RE` extracts
  candidate tokens from every normalised line; `_try_decode_base64()` decodes each as UTF-8;
  the decoded text is re-scanned through the full `_SECRETS` pattern table. This seals attack
  vector S2 from the Quartz Tribunal: a GitHub PAT encoded as Base64 in YAML frontmatter now
  triggers Z201 and exits 2. False-positive guard: minimum token length 20 chars before decoding.
  New imports: `base64`, `binascii`.

- **`os.path.normcase` portability fix in `resolver.py` (CEO-203 / KL-002).** The Shield
  boundary comparison now applies `os.path.normcase` to both the target path and the
  precomputed `_allowed_root_pairs_nc` / `_repo_root_nc_*` slots. On Linux, `normcase` is
  identity — no behaviour change. On macOS (APFS) and Windows (NTFS), mixed-case legitimate
  paths no longer produce false-positive PathTraversal outcomes. The original `target_str`
  is preserved for file lookup. Three new `__slots__` added.

- **Act 19 "The Base64 Shadow" in `zenzic lab`.** Demonstrates the S2 attack vector sealed
  by CEO-194. `expected_breach=True`. Scoring Scenarios section extended to `range(17, 20)`.
  Error strings in `parse_act_range` updated from `0–18` → `0–19`.

- **Fixture `examples/scoring/security-base64/`** (2 files): `zenzic.toml` + `secret.md`
  with a Base64-encoded GitHub PAT in YAML frontmatter. Used by Act 19.

- **`docs/explanation/audit-v070-quartz-siege.mdx`** (EN + IT) published in zenzic-doc.
  Diátaxis Explanation page — "The Quartz Tribunal" Libro Bianco documenting the AI-driven
  security audit: 3 attack vectors, 7 bugs sealed, certification metrics.

#### Fixed

- **README EN+IT:** Shield paragraph updated — Base64 speculative decoding sentence added.

- **`finding-codes.mdx` Z201 EN+IT:** Technical Context rewritten to describe the multi-phase
  scan (raw + normalised + Base64 speculative decoding).

#### Tests

- `test_shield_obfuscation.py::TestBase64Bypass` — **replaced** (was a known-limitation
  placeholder). 4 new tests: `test_base64_github_pat_detected` (canonical CEO-201 vector),
  `test_base64_aws_key_detected`, `test_base64_short_string_no_false_positive`,
  `test_base64_innocent_prose_no_false_positive`.

- `test_resolver.py::TestNormcasePortability` — 3 new tests verifying the KL-002 portability
  fix: legitimate uppercase-root resolves cleanly; traversal with mixed case still blocked;
  normcase does not open a gap via extra allowed roots.

- **1,307 passing · 0 failing · 80.28% coverage** (Python 3.11 / 3.12 / 3.13).

---

### D091 — Quartz Brand Integrity (Z107 · Z505 · Z905)

#### Added

- **`CircularAnchorRule` (Z107 CIRCULAR_ANCHOR).** New `BaseRule` subclass detecting
  self-referential anchor links (`[text](#heading)` where `heading` resolves to the
  same page). Slugifies all headings via the same `_slugify()` helper and matches
  against local anchor links. Exit 1, suppressible.

- **`UntaggedCodeBlockRule` (Z505 UNTAGGED_CODE_BLOCK).** New `BaseRule` subclass
  detecting fenced code blocks with no language specifier. Implements the CommonMark
  fence invariant: a closing fence must have an empty info string. Any non-whitespace
  in the info string is treated as an opener — Docusaurus metadata
  (e.g. `` ```python title="file.py" showLineNumbers ``) is correctly handled.
  Exit 1, suppressible.

- **`BrandObsolescenceRule` (Z905 BRAND_OBSOLESCENCE).** New `BaseRule` subclass
  scanning for obsolete release identifiers. Configured via `[project_metadata]` in
  `zenzic.toml`. Lines containing the token `[HISTORICAL]` are silently skipped.
  File patterns in `obsolete_names_exclude_patterns` (default: `CHANGELOG*.md`) are
  fully exempt. Exit 1, suppressible. Pickle-safe (module-level class; no module stored
  as instance attribute).

- **`ProjectMetadata` Pydantic model** in `src/zenzic/models/config.py`.
  Fields: `release_name: str`, `obsolete_names: list[str]`,
  `obsolete_names_exclude_patterns: list[str]` (default: `["CHANGELOG*.md", "CHANGELOG*.archive.md"]`).
  Integrated into `ZenzicConfig` and `_HANDLED_SECTIONS`.

- **Z107, Z505, Z905 registered** in `src/zenzic/core/codes.py`. All three:
  `primary_exit=1, non_suppressible=False`.

- **`_build_rule_engine()` in `scanner.py`** always adds `CircularAnchorRule` and
  `UntaggedCodeBlockRule`; conditionally appends `BrandObsolescenceRule` when
  `obsolete_names` is non-empty.

- **`zenzic init`** TOML template includes a commented `[project_metadata]` block.

- **CEO-138 info string semantics.** `has_tag = bool(info.strip())` — any non-whitespace
  character in the fence info string marks a block as tagged.

- **CEO-140 CommonMark closing fence invariant.** Closing fence requires: same character
  as opener, length ≥ opener, **empty info string** (`not info`). This eliminated 10
  false Z505 positives in architecture.mdx — a fence line with any non-whitespace info
  is always an opener, never a closer.

#### Tests

- 18 new tests across `TestCircularAnchorRule`, `TestUntaggedCodeBlockRule`,
  `TestBrandObsolescenceRule` (including 3 CEO-138/140 edge cases).
  **1 281 passing · 0 failing · 80.81% coverage.**

---

### D090 — The UX-Discoverability Law (Navbar + Footer Navigation Harvesting)

#### Added

- **Unified Navigation Discovery — Docusaurus Multi-Source Harvester.**
  `_parse_config_navigation()` added to `_docusaurus.py`. Reads `docusaurus.config.ts`
  via pure-Python regex (Pillar 2 — no Node.js) and extracts `to:` URL paths and
  `docId:` attributes from both `themeConfig.navbar.items` **and**
  `themeConfig.footer.links`. `to:` values are resolved by stripping `baseUrl` and
  `routeBasePath` prefixes, then probing for `.md` / `.mdx` on disk. Non-doc links
  (blog, external URLs) never match a file and are silently dropped.

- **`DocusaurusAdapter.get_nav_paths()` is now a true Multi-Source Aggregator.**
  Returns `sidebar_paths | navbar_paths | footer_paths`. A file is classified
  `ORPHAN_BUT_EXISTING` only when absent from all three UI navigation surfaces
  (sidebar, navbar, footer) — implementing the **UX-Discoverability Law (R21)**:
  *a file is REACHABLE if any user-clickable surface declares it*.

- **`_navbar_paths: frozenset[str]`** stored eagerly by `from_repo()` so that
  `get_nav_paths()` remains a pure aggregator with no I/O.

- **Act 7 fixture expanded** (`docusaurus-v3-enterprise`):
  - `sidebars.ts` — explicit sidebar (intro + guide/*, no changelog or about).
  - `docs/changelog.mdx` — linked from navbar only → expected REACHABLE.
  - `docs/about.mdx` — linked from footer only → expected REACHABLE.
  - `docusaurus.config.ts` — updated with `themeConfig.navbar` and `themeConfig.footer`.

- **`engines.mdx`** — new "Unified Navigation Discovery" section documenting the 3-source
  aggregation, the UX-Discoverability Law, and the `ORPHAN_BUT_EXISTING` contract.
  Source-only analysis description updated. "Dynamic sidebar plugins" wording generalised
  to "Dynamic nav plugins".

#### Architecture

- **MCP Audit finding recorded:** In Docusaurus, routing is file-system driven — all
  files in `docs/` receive a URL regardless of sidebar/navbar/footer configuration.
  Navigation surfaces are UX-discoverability constructs only. Zenzic's orphan model is
  **discoverability-based**, not URL-existence-based. MkDocs and Zensical adapters
  confirmed architecturally complete — `nav:` is the authoritative routing source for
  those engines.

- **Core purity maintained:** `validator.py` contains no reference to "navbar",
  "sidebar", or "footer". The Core calls `adapter.get_nav_paths()` — period.

#### Tests

- 14 new tests: `TestParseConfigNavigation` (NCF-01..10) + `TestUnifiedNavigation` (NCI-01..04).
  **1 260 passing · 0 failing.**

---

### D085 — Full-Spec Alignment (Docusaurus Sidebar Parser + Close #52)

#### Added

- **Docusaurus static sidebar parser — Issue #47 closed.**
  `DocusaurusAdapter.get_nav_paths()` now reads `sidebars.ts` or `sidebars.js` via a
  pure-Python regex parser (Pillar 2 — no Node.js). If any sidebar uses
  `type: 'autogenerated'`, all files remain `REACHABLE` (current behaviour preserved).
  When the sidebar is explicit, only listed doc IDs resolve to `REACHABLE`; unlisted
  pages are correctly classified as `ORPHAN_BUT_EXISTING`. Residence detection uses
  file-existence as truth — false positives from label strings are naturally filtered.
  `from_repo()` discovers `sidebars.ts` / `sidebars.js` at the repo root automatically.

#### Fixed / Closed

- **Issue #52 (SARIF output)** closed — already implemented in the D081/D082 sprint.
  `_shared.py` contains the full SARIF 2.1.0 formatter; `_check.py` exposes
  `--format sarif` on all five check commands. No further code changes needed.

#### Tests

- 14 new tests: `TestParseSidebars` (SBP-01..10) + `TestFromRepoSidebar` (SBI-01..04).
  **1 246 passing · 0 failing.**

---

### Quartz Maturity — Sovereignty & Documentation (Direttive CEO-102/103-B)

#### Added

- **Sovereign Memory Architecture — `ZENZIC_BRAIN.md` (CEO-103-B).** Agent instructions
  migrated from `.github/copilot-instructions.md` to a root-level `ZENZIC_BRAIN.md` master
  file across all three repositories (core, doc, action). A `shadow_sync()` function in
  each map script (`scripts/map_project.py`, `map_docs.py`, `map_action.py`) automatically
  propagates the master to `.github/copilot-instructions.md` after every `just map-update`
  invocation. IDE compatibility is preserved while sovereignty is established.

- **Mineral Path Release Philosophy — `docs/explanation/mineral-path.mdx` (CEO-102).** New
  Explanation page (EN + IT) documenting the geological release naming philosophy:
  Obsidian → Quartz → Basalt → Graphite → Diamond. Establishes the long-term roadmap
  narrative and the principles behind each milestone codename.

- **Quartz Clarity Rebrand (CEO-090).** Global replacement of "Obsidian" brand with
  "Quartz/Sentinel" across all production-visible surfaces in core, doc, and action repos.
  Historical references (blog slugs, tag keys, CHANGELOG pre-v0.7.0 entries) preserved as
  permanent invariants.

---

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

### The Quartz Mirror Pass: Lab, Shield & Docs Alignment (Direttive 082–086)

#### Added

- **Z404 CONFIG_ASSET_MISSING (Direttiva 085).** The Docusaurus adapter now statically
  analyses `docusaurus.config.ts` and verifies that every `favicon:` and `image:`
  (OG social card) path resolves to a real file inside `static/`. Implemented as
  `check_config_assets()` in `_docusaurus.py` — pure regex, zero subprocess. Code
  registered in `codes.py`; wired via `_AllCheckResults.config_asset_issues` in
  `cli.py`. Severity: `warning` (promote to Exit 1 via `--strict`).
- **Lab Sentinel Seal (Direttiva 086).** Every `zenzic lab <N>` run now closes with
  a dedicated **Sentinel Seal** panel (indigo border, Sentinel Palette colours) showing
  file count, elapsed time, throughput in files/s, and a per-act pass/fail verdict.
  Full-run summaries (`zenzic lab` with all acts) render an aggregate Sentinel Seal
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

### Quartz Maturity Pass: UX Hardening & Truth Audit (Direttive 076–079)

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
  *from* that target, not the *location* of it.
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

- **Agent Instruction Zenzic Ledger (Direttive CEO 046–047 — "The Knowledge Refactoring" / "The Knowledge Trinity").**
  All three repository `.github/copilot-instructions.md` files rewritten into the Zenzic Ledger
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

### Quartz Memory Law & Precision Polish Sprint (D048–D049 — 2026-04-25)

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

- **`[CLOSING PROTOCOL]` — Quartz Memory Law codified (Direttiva CEO 049 — "The Quartz Memory Law").**
  All three repository agent instruction files receive a `[CLOSING PROTOCOL]` section, placed
  immediately after `[MANIFESTO]`. Defines a mandatory per-repo checklist (update instructions,
  update changelogs, run staleness audit, run verification gate). Skipping any step is a Class 1
  violation (Technical Debt). Resolves the "Paradosso del Custode senza Memoria".
  Memory Law in `[POLICIES]` upgraded to "The Custodian's Contract" with the Class 1 violation
  clause and explicit "Definition of Done" invariant.

---

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

  Rule R13 (CEO-050) codified in `[POLICIES]`: *"Never ask the user to exclude them manually."*

#### Tests

- `tests/test_exclusion.py::TestSystemFileGuardrails` — 5 new tests: exact name exclusion,
  glob pattern exclusion (`eslint.config.mjs`), `*.lock` pattern, adapter metadata L1b, and
  non-exclusion of legitimate doc files.
- `tests/test_scanner.py::test_find_unused_assets_skips_system_infrastructure_files` — L1a end-to-end.
- `tests/test_scanner.py::test_find_unused_assets_skips_adapter_metadata_files` — L1b end-to-end.

---

### Documentation as an Invariant Sprint (D051 — 2026-04-25)

#### Changed

- **`[CLOSING PROTOCOL]` Step 3 renamed to "Staleness & Testimony Audit" in all three Zenzic Ledgers.**
  Per-repo trigger checklists added: every changed function must be cross-referenced against the
  corresponding `.mdx` page before a sprint is closed.

- **Documentation Law — "The Quartz Testimony" added to `[POLICIES]` in all three Zenzic Ledgers.**
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
  All three Zenzic Ledgers (`.github/copilot-instructions.md` in core, zenzic-doc, and
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
  `Scanning: <resolved-target>` after the Sentinel header when `PATH` is provided.
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

### The Quartz Hygiene (D063 — 2026-04-25)

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

### D073 — The Law of Evolutionary Curation (2026-04-25)

#### Governance

- **All three Zenzic Ledgers refactored from "historical diaries" to "operational manuals".**
  [CHRONICLES] section (14 bug post-mortems) removed from core ledger; lessons already
  distilled into [POLICIES] rules (R11–R18) and ADR entries remain. [SPRINT LOG] replaced
  by [ACTIVE SPRINT] (2-sprint rolling window) across all three repos.
  Law of Evolutionary Curation codified in [POLICIES]: this file is a Working Context, not
  a historical archive. Size guardrail: trigger curation when file exceeds 400 lines.

- **Rule R19 — No Domain-Level URL Exclusions (new).**
  `excluded_external_urls` in `zenzic.toml` must target specific URLs or prefixes, not
  entire domains. A blanket domain exclusion (e.g. `"https://zenzic.dev/"`) creates a
  permanent blindspot that survives content restructures. Governance only; no runtime
  validation. Documented in core ledger [POLICIES] and in `zenzic-doc` configuration
  reference.

- **ADR-006 extended with BUG-014 SPDX corollary.**
  `_first_content_line()` applies the same three-phase skip (HTML comments → frontmatter →
  blank lines) established in D072. The lesson is now permanently captured in ADR-006.

---

### D074+D075 — Coverage Iron Gate + R19 Testimony (2026-04-25)

#### Tests — D074

- **Three targeted unit tests for `_first_content_line()` multi-line comment paths.**
  The D072 three-phase walker implementation had uncovered continuation branches.
  The existing regression test only exercised single-line HTML comments.

  New tests:
  - `test_short_content_pointer_skips_multiline_html_comment` — multi-line `<!-- … -->`
    spanning 3 lines; verifies pointer lands on prose, not on any comment line.
    Covers the `in_html=True` continuation path (lines 209–213, 221 in scanner.py).
  - `test_short_content_pointer_skips_multiline_mdx_comment` — multi-line `{/* … */}`
    spanning 3 lines; verifies pointer lands on prose, not on any comment line.
    Covers the `in_mdx=True` continuation path (lines 214–218, 226 in scanner.py).
  - `test_short_content_pointer_unclosed_frontmatter` — frontmatter with no closing `---`;
    verifies no crash and `line_no ≥ 1`.
    Covers the `if i < n:` False branch (line 239 → 243 in scanner.py).

  Overall test coverage: **79.82% → 80.00%** (Python 3.11, 3.12, 3.13).

#### Documentation — D075

- **Rule R19 `:::warning` admonition added to `configuration-reference.mdx` (EN + IT).**
  The `excluded_external_urls` section now carries a permanent governance warning against
  domain-level exclusions. Law of Contemporary Testimony satisfied: R19 (codified in D073)
  is now visible at the point of use in the official reference documentation.

---

### D077 — The Machine-to-Machine Silence (2026-04-25)

#### Fixed

- **`_print_no_config_hint()` was contaminating SARIF/JSON output on stdout (Rule R20).**
  When `zenzic check all --format sarif` ran against a project without `zenzic.toml`,
  the Rich informational panel (the "no config" hint) was written to stdout before the
  SARIF JSON, producing a file starting with `╭` — invalid JSON that crashed GitHub Code
  Scanning with `Unexpected token '╭'`.

  Fix: `_print_no_config_hint(output_format: str = "text")` in `_shared.py` now gates on
  `_MACHINE_FORMATS = frozenset({"json", "sarif"})` — returning immediately without any
  stdout write for machine formats. Five call sites in `_check.py` updated to pass the
  current `output_format`. `check all --format sarif` stdout now starts with `{`.

  **Rule R20 — Machine Silence** codified in [POLICIES]: any machine-readable format
  (json/sarif) mandates the total suppression of Rich banners and panels on stdout.

#### Action (zenzic-action)

- **`github/codeql-action/upload-sarif@v3` → `@v4`** (deprecation fix).
- **`astral-sh/setup-uv@v7` → `@v8`** (cache improvements).
- **`version` input default changed from `latest` → `0.7.0`** (stability-first default).
  Users who want continuous updates can explicitly set `version: latest`.

---

### D084 — The Quartz Neutrality Audit (2026-04-26)

#### Changed — `docs/reference/engines.mdx` (EN + IT mirror)

- **MkDocs `### Route URL resolution` subsection added.** Documents that Zenzic validates
  source-level relative links, making link correctness immune to `use_directory_urls` mode.
  Absolute links (`/path/`) remain always flagged as `Z105 ABSOLUTE_PATH`.

- **Zensical Transparent Proxy section rewritten and elevated.**
  - `:::warning[Structural Custodian Rule]` replaced with `:::tip[Migration strategy]` — framing
    corrected from "safety net" to "signature migration feature".
  - Anchor `{#zensical-transparent-proxy}` added for deep-linking.
  - Bridge mapping table: 4 `mkdocs.yml` fields → what `ZensicalAdapter` uses them for
    (`docs_dir`, `nav`, `plugins.i18n.languages`, `theme.favicon`/`theme.logo`).

- **Zensical `### Limitations` subsection added.** Covers plugin-generated nav, static TOML
  parsing, and `zensical.toml` discovery scope.

- **Standalone section expanded from 17-line stub to full section (~43 lines).** Four subsections:
  `### When to use Standalone` (3 use-cases), `### Minimal configuration` (TOML block),
  `### Capabilities` (full-strength checks listed), `### Limitations` (orphan check disabled,
  locale suppression pattern).

#### Added

- **`README.md`: HN Hook.** Direct link to `https://zenzic.dev/blog/beyond-the-siege-zenzic-v070`
  added under "The Zenzic Chronicles" section.

---

### D083 — The Iron Gate & Sibling Automation (2026-04-26)

#### Added — Coverage Iron Gate

- **3 targeted CLI tests in `tests/test_cli.py`** pushing total coverage to **80.07%** (1232 tests):
  - `test_inspect_capabilities_shows_bypass_table` — verifies Section C bypass table renders with
    `"Engine-specific Link Bypasses"`, `"pathname:"`, `"docusaurus"`, and `"R21"` in output.
  - `test_score_perfect_shows_obsidian_seal` — mocks `_run_all_checks` returning score=100;
    asserts `"OBSIDIAN SEAL"` and `"Every check passed"` appear in output.
  - `test_score_low_uses_error_style` — mocks score=30; covers line 132 (`STYLE_ERR` branch);
    asserts Sentinel Seal does NOT appear.

#### Added — Sibling Automation

- **`zenzic-doc/noxfile.py`** — 5 nox sessions: `lint` (TypeScript + Markdown), `typecheck`,
  `build` (production Docusaurus), `reuse` (REUSE/SPDX), `preflight` (full pipeline).
  Provides a unified `nox -s preflight` entry point mirroring the Core repo.

- **`zenzic-action/noxfile.py`** — 3 nox sessions: `reuse`, `check` (Zenzic self-audit),
  `preflight`. Gives the Action the same automation discipline as the Core.

- **`zenzic-action/justfile`** — 5 commands: `bump`, `reuse`, `check`, `preflight`, `clean`.

- **`zenzic-action/scripts/bump-version.sh`** — Bash script to sync the Zenzic version
  default in `action.yml` with a single command (`just bump 0.7.1`). Validates version
  format; idempotent; produces a clear change summary.

#### Fixed — `zenzic-action` REUSE Compliance

- Added `LICENSES/Apache-2.0.txt`, `.reuse/dep5` (covers `package.json` and SVG assets),
  and SPDX header to `.github/copilot-instructions.md`. Now 12/12 files compliant.

---

### D082 — The Final Quartz Polish (2026-04-26)

#### Added

- **`zenzic inspect capabilities`: Section C "Engine-specific Link Bypasses".**
  New third table showing which built-in engine declares which URI scheme bypasses via
  `get_link_scheme_bypasses()`. Table rows: `docusaurus` → `pathname:` (static-asset routing
  escape hatch), `mkdocs` / `zensical` / `standalone` → `(none)`. Rule R21 footer note added.
  Command help string updated from "built-in scanners and registered plugin rules" to include
  "engine-specific link bypasses".

- **`zenzic score`: Sentinel Seal panel at 100/100.**
  When `report.score == 100`, the score command now displays the same celebratory Sentinel Seal
  panel as Lab Act 0 — `Group` with `ObsidianPalette.BRAND` shield header and a success line
  confirming documentation integrity. Panel is suppressed in `--format json` mode.

#### Verified Complete

- **`docs/how-to/add-badges.mdx` (EN) lines 73-111** already document the full dynamic badge
  workflow: `zenzic score --save` → `.zenzic-score.json` → GitHub Actions with
  `dynamic-badges-action` → Shields.io endpoint. No changes required.

---

### D081 — The War Room Examples (2026-04-26)

#### Added — Cross-Engine Validation Matrix

- **`examples/matrix/red-team/` — three attack-vector fixtures (standalone, mkdocs, zensical).**
  Each fixture contains identical attack vectors: Z201 (Shadow Secret — `aws_access_key_id` in YAML
  frontmatter), Z105 (Absolute Trap — three absolute-path links), Z502 (Short Content Ghost — four
  files under 50 words), Z501 (Ghost File — `draft: false`), Z401 (Missing Index — four
  subdirectories without `index.md`). All three produce identical findings. **Exit code: 2 (SECURITY BREACH).**

- **`examples/matrix/blue-team/` — three clean documentation fixtures (standalone, mkdocs, zensical).**
  Fixed versions: relative links, ≥50-word prose, `index.md` in every subdirectory, no credentials,
  `draft:` field removed. All three earn the Sentinel Seal. **Exit code: 0 (Sentinel Seal ✨).**
  Parity confirmed: zero asymmetries across engines.

#### Documentation (zenzic-doc)

- **`architecture.mdx` (EN+IT): "Protocol Sovereignty" and "Cross-Engine Validation Parity" subsections**
  added after the Built-in Adapters table. Documents `get_link_scheme_bypasses()`, Rule R21, and
  the D079 parity guarantee with a per-engine table. References `examples/matrix/` as living proof.

- **`implement-adapter.mdx` (EN+IT): Step 6 "Declare Link-Scheme Bypasses" added;**
  Adapter Contract Guarantee item 11 for `get_link_scheme_bypasses()` added.

- **`first-audit.mdx` (EN+IT): Step 2 restructured to "The Siege & The Shield".**
  Shows `uvx zenzic lab 2` (Security Breach banner) first, then `uvx zenzic lab 0` (Sentinel Seal).
  Implements Rule R22 (Fall-before-Redemption): emotional contrast is the lesson.

#### Governance

- **Rule R22 (Fall-before-Redemption) codified in [POLICIES]:** tutorial content must show the
  broken state first (The Siege), explain the fix, then show the passing state (The Sentinel Seal).

---

### D079+D080 — The Agnostic Siege + Protocol Sovereignty (2026-04-26)

#### Refactored — D080: Protocol Sovereignty

- **`validator.py` Core Leak removed — `BaseAdapter.get_link_scheme_bypasses()` introduced.**
  `validator.py` contained two hardcoded references to `"docusaurus"` (lines 724–725 and 793–796)
  that exposed the `pathname:` escape hatch via string comparison on the engine name.
  Per Direttiva CEO 080 (Protocol Sovereignty), the Core must be engine-agnostic — it must know
  the Protocol, not the actors.

  **Changes:**
  - `_DOCUSAURUS_SKIP_SCHEMES = ("pathname:",)` constant removed from `validator.py`.
  - `get_link_scheme_bypasses() -> frozenset[str]` added to `BaseAdapter` protocol (`_base.py`).
  - All four adapters implement the new method:
    - `DocusaurusAdapter`: returns `frozenset({"pathname"})` — preserves the `pathname:///` escape hatch (Rule R16, CEO-055).
    - `MkDocsAdapter`, `ZensicalAdapter`, `StandaloneAdapter`, `ZensicalLegacyProxy`: return `frozenset()`.
  - `validate_links_async()` now derives `_bypass_schemes` from `adapter.get_link_scheme_bypasses()` immediately after adapter instantiation (line 622). `_effective_skip` is built as `_SKIP_SCHEMES + tuple(f"{s}:" for s in _bypass_schemes)`.
  - Z105 absolute-path check: `if parsed.path.startswith("/") and parsed.scheme not in _bypass_schemes:` — no engine string in sight.
  - `test_docusaurus_adapter.py`: `test_pathname_in_docusaurus_skip_schemes` updated to assert
    `DocusaurusAdapter.get_link_scheme_bypasses()` contains `"pathname"` (constant-free test).

  **Invariant:** Adding a new engine adapter tomorrow requires **zero changes** to `validator.py`.

#### Lab — D079: The Agnostic Siege (Cross-Engine Parity Matrix)

- **Three external demo repos scaffolded in `/dev/PythonSandbox/`:**
  `zenzic-demo-standalone/`, `zenzic-demo-mkdocs/`, `zenzic-demo-zensical/` — each embedding
  four deliberately crafted attack vectors against identical documentation content.

  **Attack Vectors:**

  | Vector | Rule | File |
  |---|---|---|
  | Shadow Secret | Z201 | `docs/how-to/configure.md` — fake AWS key `AKIAIOSFODNN7EXAMPLE` in YAML frontmatter |
  | Absolute Trap | Z105 | `docs/reference/api.md`, `docs/how-to/configure.md`, `docs/tutorial/getting-started.md` — `/absolute/path` links |
  | Short Content Ghost | Z502 | `docs/explanation/architecture.md` — 12 frontmatter lines, 2 prose words |
  | Missing Index | Z401 | All 4 subdirectories (`tutorial/`, `how-to/`, `reference/`, `explanation/`) — no `index.md` |

  **Parity Matrix Results (from demo dir + Sovereign Scan from core repo):**

  | Engine | Z201 | Z105 | Z502 | Z401 |
  |---|---|---|---|---|
  | standalone | ✅ exit 2 | ✅ 3× | ✅ 4 files | ✅ 4× info |
  | mkdocs | ✅ exit 2 | ✅ 3× | ✅ 4 files | ✅ 4× info |
  | zensical | ✅ exit 2 | ✅ 3× | ✅ 4 files | ✅ 4× info |

  **Verdict: ZERO asymmetries.** All three engines produce identical finding counts and severities
  for the same documentation content. Sovereign Root Protocol confirmed: running
  `uv run zenzic check all ../zenzic-demo-X` from the core repo loads the demo's config,
  not the core's `zenzic.toml`.

  **Bonus Discovery:** Z501 (placeholder text) fires on `draft: false` in `architecture.md`
  frontmatter — the `draft` keyword matches the default placeholder pattern. This is consistent
  across all three engines (by design: it's a content rule, not an engine rule).

---## [0.6.1] — 2026-04-19 — Obsidian Glass [SUPERSEDED]

> ⚠ **[SUPERSEDED by v0.7.0]** — Version 0.6.1 is deprecated due to alignment issues with Docusaurus specifications and legacy terminology. All users must upgrade to v0.7.0 "Obsidian Maturity".

---

### Breaking Changes

- **Standalone Engine replaces Vanilla (Direttiva 037).** The `VanillaAdapter` and the
  `engine = "vanilla"` keyword have been removed. All projects must migrate to
  `engine = "standalone"`. Any `zenzic.toml` still using `engine = "vanilla"` will
  raise a `ConfigurationError [Z000]` at startup with a clear migration message.
  *Migration:* replace `engine = "vanilla"` with `engine = "standalone"` in your
  `zenzic.toml` or `[tool.zenzic]` block.

---

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

---

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

---

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

---

### Added

- **`--format json` on individual check commands.** `check links`, `check orphans`,
  `check snippets`, `check references`, and `check assets` now accept `--format json`
  with a uniform `findings`/`summary` schema. Exit codes are preserved in JSON mode.
  ([#55](https://github.com/PythonWoods/zenzic/pull/55) — contributed by [@xyaz1313](https://github.com/xyaz1313))
- **Shield: GitLab Personal Access Token detection.** The credential scanner now
  detects `glpat-` tokens (9 credential families total).
  ([#57](https://github.com/PythonWoods/zenzic/pull/57) — contributed by [@gtanb4l](https://github.com/gtanb4l))

---

### Fixed

- **JSON exit-code asymmetry in `check orphans` and `check assets`.** Both commands
  now distinguish `error` vs `warning` severity before deciding exit codes, consistent
  with `check references` and `check snippets`. Previously, any finding (including
  warnings) triggered Exit 1 in JSON mode.

## [0.6.1rc1] — 2026-04-15 — Obsidian Bastion

---

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

---

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

---

### Changed

- **BREAKING (Alpha):** `exclusion_manager` parameter is now mandatory on
  `walk_files`, `iter_markdown_sources`, `generate_virtual_site_map`,
  `check_nav_contract`, and all scanner functions. No backward-compatible
  `None` default.

## [0.6.0a2] — 2026-04-13 — Obsidian Glass (Alpha 2)

---

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

---

### Changed

- **BREAKING: `excluded_assets` uses fnmatch** — All entries are now
  interpreted as glob patterns.  Plain literal paths still match (they are
  valid patterns), but patterns like `**/_category_.json` or `assets/brand/*`
  are now supported natively.  The previous set-subtraction implementation
  has been removed.

---

### Fixed

- **Docusaurus “dynamic patterns” warning emitted twice** — When
  `base_url` is declared in `zenzic.toml`, the adapter no longer calls
  `_extract_base_url()`, suppressing the duplicate warning entirely.

## [0.6.0a1] — 2026-04-12 — Obsidian Glass

> **Alpha 1 of the v0.6 series.** Zenzic evolves from a MkDocs-aware linter into
> an **Analyser of Documentation Platforms**. This release introduces the
> Docusaurus v3 engine adapter — the first non-MkDocs/Zensical adapter — and
> marks the beginning of the Obsidian Bridge migration strategy.

---

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

---

### Testing

- **`tests/test_docusaurus_adapter.py` — 65 tests across 12 test classes.**
  Full coverage of the Docusaurus adapter refactor: config parsing (CFG-01..07),
  `routeBasePath` extraction (RBP-01), frontmatter slug support (SLUG-01),
  dynamic config detection, comment stripping, `from_repo()` integration,
  URL mapping regression, and route classification regression.
