<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to Zenzic are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

> **Development history (v0.1.0 – v0.6.x):** See the [Changelog Archive](CHANGELOG.archive.md).

## [0.7.0] — 2026-05-07 — Quartz Maturity (Stable)

> **Legacy Documentation:** Versions prior to v0.7.0 are officially deprecated and do not follow
> the current Diátaxis architecture. For historical reference, see the
> [v0.6.1 GitHub Release](https://github.com/PythonWoods/zenzic/releases/tag/v0.6.1).
> The authoritative source is [zenzic.dev](https://zenzic.dev).

### 💎 Quartz Era (Initial Release)

This release marks Year Zero for the Zenzic ecosystem, establishing a new standard of
deterministic maturity and formal integrity. The codebase achieves structural maturity:
1,342+ tests, 80%+ branch coverage, and a hardened security pipeline.

#### Added

- **Z204 FORBIDDEN_TERM — Enterprise Privacy Gate (Sprint D100)**: New Shield rule that
  triggers Exit 2 when a forbidden project term appears in any documentation file. Patterns
  (plain strings or anchored regexes) are declared in the machine-local, git-ignored
  `.zenzic.local.toml`, keeping sensitive project vocabulary permanently off `git log`.
  Two-layer architecture: `scan_line_for_forbidden_terms()` in `shield.py` handles the
  term scan; `_apply_local_toml()` in `config.py` merges patterns additively at load time.
- **`.zenzic.local.toml` init scaffolding (Sprint D100)**: `zenzic init` (and `--dev`)
  always creates `.zenzic.local.toml` and appends it to `.gitignore` automatically, so
  private patterns are git-ignored from the first commit.

- **EPOCH 7a.1 — Zero-Config Sovereignty (`absolute_path_allowlist` purged)**: The
  `[link_validation]` TOML schema and its `absolute_path_allowlist` field are
  removed. Multi-instance Docusaurus plugin URL prefixes (`/docs/`, `/developers/`,
  every additional `@docusaurus/plugin-content-docs` instance) are now auto-detected
  by `DocusaurusAdapter.get_absolute_url_prefixes(repo_root)` — a new Protocol
  method on `BaseAdapter`. Two pure-Python passes preserve the Zero Subprocess
  invariant: a regex-based static parse of `docusaurus.config.{ts,js,mjs,cjs}` that
  walks every `@docusaurus/plugin-content-docs` tuple and harvests its
  `routeBasePath`, plus a filesystem heuristic that pairs `<repo>/<id>/` content
  trees with `i18n/<locale>/docusaurus-plugin-content-docs-<id>/` siblings when
  the config is dynamic. Z105 `ABSOLUTE_PATH` honours the discovered prefixes
  without any user-side TOML duplication. **Industry-grade — no compat shim**:
  `LinkValidationConfig` is removed in full; configs that still declare
  `[link_validation]` will fail TOML validation.
- **Zero-Config Asset Defaults (CEO Directive — Asset Cemetery)**: Universal
  toolchain files are promoted to Layer 1 in `SYSTEM_EXCLUDED_FILE_NAMES` and
  `SYSTEM_EXCLUDED_FILE_PATTERNS` — `*.toml`, `*.yaml`, `*.yml`, `*.json`,
  `*.cfg`, `*.ini`, `*.cff`, `*.code-workspace`, `LICENSE`, `LICENSE.txt`,
  `LICENSE.md`, `NOTICE`, `NOTICE.txt`, `COPYING`, `Dockerfile`, `noxfile.py`,
  `.gitignore`, `.gitattributes`, `.coverage`. "Prose-only Maintenance" repos
  (engine `standalone` with `docs_dir = "."`) no longer need to repeat them in
  `excluded_assets`.
- **Zero-Config Directory Defaults (CEO Directive — Dir Cemetery)**: Universal
  build / temporary artefact directories are promoted to `SYSTEM_EXCLUDED_DIRS`
  — `build`, `dist`, `temp`, `tmp`, `mutants` (`.tox` was already there). Every
  Python wheel build, JS bundler, and mutation-testing toolchain is honoured
  Zero-Config from now on.
- **EPOCH 7a — Multi-Root Discovery (VSM Blindness sealed)**: The VSM is no longer
  bounded by `docs_dir`. Adapters can now declare extra content roots via the optional
  `get_extra_content_roots(repo_root) -> list[ContentRoot]` hook (discovered via
  `hasattr()`, mirroring `get_locale_source_roots` — non-breaking for third-party adapters).
  The Docusaurus adapter auto-detects the `blog/` plugin in two pure-parsing passes
  (static regex over `docusaurus.config.{ts,js,mjs,cjs}` then convention fallback) — the
  Zero Subprocess invariant is preserved. Four pipeline stages (Discovery, VSM, Validator,
  Scanner Z903/Z104) cooperate so blog posts behave as first-class content: broken links
  inside `blog/` and cross-tree links from `docs/` to `blog/` are now caught by
  `zenzic check all --strict` instead of slipping through to `docusaurus build`. A
  Reverse-Mapping invariant test (`tests/test_docusaurus_blog_vsm.py::TestEpoch7aReverseMapping`)
  asserts every blog `Route.source` traces back to a real file on disk, locking the
  contract that EPOCH 7b virtual routes (tags, pagination, authors) will inherit.
  Discovery uses `walk_files` (the existing `os.walk` engine), not `rglob` — determinism
  is preserved.
- **EPOCH 7b — Virtual Routes & `zenzic inspect routes` (The JSON API)**: Engine-generated
  pages — Docusaurus tag pages (`/blog/tags/{slug}/`), tag index (`/blog/tags/`), paginated
  indexes, and author profiles — are now first-class VSM citizens with the
  Reverse-Mapping Invariant enforced at construction time: a `VirtualRoute` with
  `source_files=frozenset()` raises `ValueError` immediately, preventing any untraced URL
  from reaching the VSM. Three new finding codes: **Z111 VIRTUAL_ROUTE_BROKEN** (error)
  when a docs link targets a tag URL that no blog post activates, **Z113 AUTHOR_KEY_COLLISION**
  (error) for duplicate author keys, **Z114 LARGE_PAGINATION_SET** (info) when the
  pagination set exceeds 200 pages. The `DocusaurusAdapter` tag generator applies Unicode
  NFKD normalisation + `re.ASCII` slugification (matching Docusaurus's own algorithm) and
  guards against pure-CJK tags returning `"untagged"`. The new CLI command
  `zenzic inspect routes [--kind physical|virtual|all] [--json]` exports the complete site
  map in a deterministic JSON format with per-route `url`, `kind`, `source_files`
  (repo-relative POSIX), and `digest` (`sha256(url + ":" + ",".join(sorted(source_files)))`).
  **JSON Purity Invariant**: when `--json` is active, `stdout` contains exclusively valid
  JSON — no ANSI codes, no banners. This feature is designed to be consumed by external
  tools: custom Bash scripts, CI/CD dashboards, or Artificial Intelligence agents that
  require architectural context.
- **Sentinel Seal**: Rigorous 4-Gates validation system (`just verify`) integrated across
  every repository — pre-commit, test-cov, and self-check run identically in local and CI.
- **Cross-Repo Governance**: Branch Parity Rule for Core/Doc synchronisation with automatic
  fallback to `main`. VS Code Multi-Root Workspace configuration for unified development.
- **Z907 I18N Parity**: Language-agnostic translation parity scanner with adaptive parallelism,
  frontmatter key enforcement, and multi-instance Docusaurus support.
- **SARIF 2.1.0 Export**: All `check` commands support `--format sarif` for native GitHub
  Code Scanning integration with inline PR annotations.
- **Cross-Platform CI Matrix**: 3×3 matrix (Ubuntu/Windows/macOS × Python 3.11/3.12/3.13).
- **Engine Auto-Discovery**: `engine = "auto"` resolves the documentation framework
  automatically (Docusaurus → MkDocs → Zensical → Standalone).
- **Base64 Speculative Decoder**: Shield detects credentials encoded as Base64 in YAML
  frontmatter, sealing the S2 attack vector from the Quartz Tribunal.
- **Z107 Circular Anchor**, **Z505 Untagged Code Block**, **Z905 Brand Obsolescence**:
  Three new rule-based checks for structural and brand integrity.
- **Z404 Config Asset Integrity**: Verifies favicon and social card paths across all
  three supported engines (Docusaurus, MkDocs, Zensical).
- **Unified Navigation Discovery**: Docusaurus orphan detection aggregates sidebar,
  navbar, and footer surfaces (UX-Discoverability Law R21).
- **Static Sidebar Parser**: Pure-Python regex parser for `sidebars.ts`/`sidebars.js`.
- **Official GitHub Action**: `PythonWoods/zenzic-action` composite action with SARIF
  upload and configurable quality gates.
- **Determinism Invariant**: Formal contract in `pyproject.toml` — Zenzic ships zero
  AI/ML inference dependencies.
- **`--exclude-url` CLI flag** (`check all`, `check links`): Runtime suppression of external
  URL validation for specific URL prefixes. Repeatable; merged with `excluded_external_urls`
  from `zenzic.toml`. Designed for CI/CD deployment paradoxes — e.g. suppressing a GitHub
  Release page that does not yet exist at pipeline time.

#### Changed

- **Engine-Agnostic Architecture**: MkDocs plugin permanently removed. Zenzic is now a
  Sovereign CLI independent of any documentation framework.
- **Windows Unicode Shield in CLI bootstrap**: `cli_main()` now invokes
  `bootstrap_unicode()` before Rich traceback and logging setup, forcing UTF-8
  stdio (`errors='replace'`) on Windows to prevent `UnicodeEncodeError`
  crashes from console code pages.
- **CLI Restructuring**: `cli.py` monolith split into a coherent `cli/` package.
  `zenzic plugins` replaced by `zenzic inspect capabilities`.
- **Layer Law Enforcement**: `ui.py` → `core/ui.py`, `lab.py` → `cli/_lab.py`,
  `run_rule()` → `core/rules.py`. Core never imports from CLI layer.
- **Pre-commit Hook**: `zenzic-check-all` replaced by `zenzic-verify` (4-Gates posture).
- **Coverage Format**: Standardised to JSON (`coverage.json`) across justfile and noxfile.
- **Core CI and automation parity**: `.github/workflows/ci.yml` now runs
  `just verify` on an Ubuntu/Windows matrix (`fail-fast: false`) and the core
  `justfile` is explicitly Bash-first (`set shell := ["bash", "-c"]`) for
  consistent recipe behavior on GitHub Windows runners. `ZENZIC_EXTRA_ARGS`
  is propagated as an env block in CI and honoured via `${ZENZIC_EXTRA_ARGS:-}`
  in the `check` recipe — enabling the Sovereign Override 404 shield without
  local configuration changes.
- **`.zenzic.dev.toml` hard-fail guard** (`config.py`): `_apply_local_toml()`
  now raises `ConfigurationError` immediately when `.zenzic.dev.toml` is found
  at repo root, with an inline migration message pointing users to `zenzic init`
  and `.zenzic.local.toml`. Eliminates ghost-config debugging surface.

#### Removed

- **`.zenzic.dev.toml` (D002 Environmental Privacy Gate) — hard removed**: The file no longer
  exists for the Zenzic engine. It is not scanned, not loaded, not warned about. The sole
  source of truth for local Privacy Gate patterns is `.zenzic.local.toml`.
  `_scaffold_dev_toml()` removed; `zenzic init --dev` calls `_scaffold_local_toml()` directly.

- **`[link_validation]` TOML schema (EPOCH 7a.1)**: The `LinkValidationConfig`
  Pydantic model and its `absolute_path_allowlist: list[str]` field are removed
  from `zenzic.models.config`. Configurations that still declare
  `[link_validation]` raise a TOML validation error. **Migration:** delete the
  block — DocusaurusAdapter discovers plugin URL prefixes Zero-Config.
- **Stale ghost paths in `excluded_build_artifacts`**: `docs/configuration/*.md`
  and `docs/adr/*.md` removed from `zenzic.toml` — the underlying directories
  were estirpated in earlier EPOCHs; the entries were dead.
- **Legacy Brand Purge**: Complete removal of all obsolete nomenclature and external
  platform references from active configuration and documentation.
- **MkDocs Plugin**: `zenzic.integrations.mkdocs` physically purged. The `[mkdocs]`
  optional extra no longer exists.
- **`zenzic plugins` command**: Entirely removed. Use `zenzic inspect capabilities`.
- **`scripts/map_project.py`**: Superseded; no remaining callers.

#### Security

- **[D100] Z204 FORBIDDEN_TERM — Brand Integrity Shield**: Two-layer Privacy Gate
  architecture seals sensitive project vocabulary (codenames, internal endpoints, PII) at
  the Shield layer (Exit 2). Patterns are declared in machine-local, git-ignored
  `.zenzic.local.toml`. `.zenzic.dev.toml` is hard-removed: unrecognised by the engine,
  never scanned, never loaded.
- **[ZRT-001]** Shield Blind Spot — YAML Frontmatter Bypass sealed (Dual-Stream architecture).
- **[ZRT-002]** ReDoS + ProcessPoolExecutor Deadlock — Canary prevention + 30s timeout containment.
- **[ZRT-003]** Split-Token Shield Bypass — `_normalize_line_for_shield()` pre-processor.
- **[ZRT-004]** Context-Aware VSM Resolution — `ResolutionContext` dataclass for nested paths.
- **[ZRT-007] DFA Revolution — Google RE2 Engine** (`core/rules.py`, `core/shield.py`): Integral
  migration to the **Google RE2** DFA engine. `CustomRule` patterns now have guaranteed $O(n)$
  complexity — ReDoS is eliminated by design, not by timeout.
  - **Breaking Change**: patterns using backreferences (`\1`), lookaheads (`(?=...)`, `(?!...)`)
    or lookbehinds (`(?<=...)`) are rejected at load time with `PluginContractError`.
  - `timeout.py` and its dependency on `signal.SIGALRM` deleted: Zenzic is now natively
    identical on Linux and Windows.
  - `shield.py` migrated to `re2`: the Shield is now fully DFA-Pure.
  - Legacy code aliases `Z001` and `Z009` removed: findings now emit `Z101` (LINK_BROKEN)
    and `Z902` (ANALYSIS_TIMEOUT) directly at the source.
- **Base64 speculative decoder** seals encoded credential attack vector.
- **`os.path.normcase` portability fix** for cross-platform Shield boundary comparison.
- **4-Gates Standard**: pre-commit → test-cov → self-check, enforced on every push.

#### Migration

Contributors must rerun bootstrap after pulling this release:

```bash
just sync
uvx pre-commit install              # commit-stage hooks
uvx pre-commit install -t pre-push  # 🛡️ Final Guard (just verify)
```

Replace `zenzic plugins list` with `zenzic inspect capabilities`.
Replace `pip install "zenzic[mkdocs]"` with `pip install zenzic`.

#### Fixed

- **[ZRT-006] VSM Bypass: Absolute Slug Links Skipped Silently** (`core/validator.py`):
  Two coordinated bugs caused Zenzic to emit no finding when an absolute link targeted
  the wrong slug of a Docusaurus blog post — while `docusaurus build` failed with a
  broken-link error.

  1. **Lifecycle ordering** — `DocusaurusAdapter.set_slug_map(md_contents)` was never
     called during `validate_links_async()`. The slug map was empty at VSM construction
     time, so blog posts with a `slug:` frontmatter field were routed via filename
     derivation (e.g. `2026-04-29-post.mdx` → `/blog/2026-04-29-post/`) instead of
     the declared slug URL. Fix: `set_slug_map()` is now called via `hasattr` guard
     immediately before `build_vsm()` — cross-engine safe, non-breaking for MkDocs /
     Standalone / Zensical adapters that do not implement the method.

  2. **Scoped VSM lookup** — The Z105 `ABSOLUTE_PATH` suppression for project-owned
     prefixes (e.g. `/blog/`) was implemented as a bare `continue`, which exited the
     per-link loop before any VSM lookup, making `FILE_NOT_FOUND` impossible to fire
     on those links. Fix: a new `_scanned_vsm_prefixes` discriminator separates
     *fully-scanned* prefixes (those with ≥1 route in the VSM) from *unscanned sibling
     plugins* (e.g. `/developers/` whose markdown is outside the scan scope). Links
     targeting a scanned prefix now receive a `dict.get()` lookup and report Z104
     `FILE_NOT_FOUND` when the exact route is absent. Unscanned prefixes retain the
     unconditional bypass — Zero-Config invariant preserved.

- **Regression lock** — `tests/test_docusaurus_blog_vsm.py::TestAbsoluteSlugMismatch`
  (2 new tests):
  - `test_absolute_broken_blog_link_is_detected` — wrong slug raises `FILE_NOT_FOUND`
  - `test_correct_absolute_slug_link_is_clean` — correct slug produces no finding

**Test suite: 1485 passed, 0 failed.**
