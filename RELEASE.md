<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# 💎 Zenzic v0.7.1 — The Quartz Era (Quartz Maturity)

This release marks the birth of the Sovereign Knowledge System. Following the Quartz Purgation, Zenzic definitively abandons all experimental residues to become a deterministic, industrial-grade infrastructure.

## 🏛️ The Pillars of v0.7.1

- **Deterministic Integrity**: Complete absence of any probabilistic dependency or logic. Zenzic now operates exclusively on structural facts and certain invariants.
- **Sentinel Seal**: A 4-stage validation system (4-Gates Standard) ensuring absolute quality before every push.
- **Cross-Repo Governance**: Implementation of the Branch Parity Rule for perfect synchronization between code and documentation.
- **Sovereign Privacy Gate**: The Z204 Enterprise Privacy Gate (`.zenzic.local.toml`) ensures
  that sensitive project vocabulary — codenames, internal endpoints, PII — never escapes the
  developer's machine. `.zenzic.dev.toml` is gone; `.zenzic.local.toml` is the only
  supported local configuration file.
- **Machine Silence**: Optimization of analysis flows for native CI/CD integration via the SARIF 2.1.0 standard.

## ⚠️ Evolution Note (Breaking Changes)

v0.7.1 is Year Zero. Previous versions are officially deprecated as they do not follow the current Diátaxis architecture. Every reference to old brands or legacy architectures has been removed to make way for a lean ecosystem focused on source purity.

## 🚀 Towards the Future

With this release, Zenzic is no longer just a tool, but a trust platform for documentation engineering.

---
**PythonWoods** <dev@pythonwoods.dev>
*Release Date: 2026-05-07*

---

## ⚠️ Breaking Changes

| Change | Migration |
| :--- | :--- |
| `.zenzic.dev.toml` hard-removed (D002 → D100 hard break) | Rename to `.zenzic.local.toml`; copy your `forbidden_patterns` into it; delete the old file. The engine does not recognise the old filename. |
| MkDocs plugin (`zenzic.integrations.mkdocs`) removed | Remove `plugins: - zenzic` from `mkdocs.yml`; add `zenzic check all` as a CI step |
| `engine = "vanilla"` removed | Replace with `engine = "standalone"` in `zenzic.toml` |
| `zenzic plugins` command removed | Use `zenzic inspect capabilities` |
| `just preflight` recipe removed; pipeline collapsed into `just verify` | Run `uvx pre-commit install -t pre-push` after `just sync` to install the new Final Guard |
| `nox -s preflight` session removed (duplicated `just verify`) | Run `just verify` locally; CI invokes the same command |
| `just test` no longer produces coverage by default (now `pytest -n auto`) | Use `just test-cov` for the audit run with `coverage.xml` |

---

## 🛡️ EPOCH 4 — The Safe Port (4-Gates Standard)

v0.7.1 introduces the **atomic single entry-point** for quality:

```bash
just verify    # locale ≡ remote — same command in pre-push hook AND GitHub Actions
```

The 4 Gates: pre-commit hooks → `pytest` with coverage (`fail_under=80`) →
`zenzic check all --strict` → exit-code parity (Shield Z201 → exit 2,
Sentinel Z202/Z203 → exit 3, non-suppressible).

### Daily flow

| Stage | Command | Speed |
|:------|:--------|:------|
| TDD inner loop | `just test` (parallel, no cov) | ⚡ instant |
| Commit | `git commit` (light hooks) | < 5 s |
| Push | `git push` → pre-push hook → `just verify` | < 60 s |
| CI | GitHub Actions runs `just verify` | identical |

### Break-Glass Protocol (D7)

`--no-verify` is **not forbidden**, but every bypass is a public event:
label `gate-bypass` + blameless post-mortem issue within 24h
(`.github/ISSUE_TEMPLATE/gate-bypass-postmortem.md`). An undocumented
("ghost") bypass is **critical technical debt** reviewed at sprint
retrospective. Transparent radically: a declared bypass is a chance to
harden the gate; a silent one is a betrayal of the Safe Port.

---

## 🌍 EPOCH 5 — Z907 I18N_PARITY (Cross-Language Integrity)

v0.7.1 closes the last gap in the documentation integrity story:
**translation drift**. A new core scanner — `Z907 I18N_PARITY` — verifies
that every base-language documentation file has a mirror in each
configured target language root, and that key frontmatter fields
(`title`, `description`, …) are present in every translation.

```toml
# zenzic.toml — language-agnostic, opt-in
[i18n]
enabled = true
base_lang = "en"
base_source = "docs"
strict_parity = true
require_frontmatter_parity = ["title", "description"]

[i18n.targets]
it = "i18n/it/docusaurus-plugin-content-docs/current"
es = "i18n/es/docusaurus-plugin-content-docs/current"

# Multi-instance: a second Docusaurus plugin (e.g. /developers) can
# declare its own base/targets pair without code changes.
[[i18n.extra_sources]]
base_source = "developers"
[i18n.extra_sources.targets]
it = "i18n/it/docusaurus-plugin-content-docs-developers/current"
```

### Highlights

- **Language-agnostic by construction.** `base_lang` and `targets[]` are
  declared in config; adding ES, FR, JA is a YAML edit, not a code change.
- **`i18n-ignore: true` frontmatter escape hatch** — drafts and
  language-specific guides opt out per-file.
- **Adaptive parallelism** — fan-outs through `ThreadPoolExecutor`
  above 50 base files (matches the existing scanner threshold).
- **Hypothesis-stressed.** Property-based tests cover deep directory
  nesting and Latin Extended unicode segments before any mass migration.

The check integrates seamlessly into `zenzic check all` and respects
`strict_parity` for the error/warning severity choice.

---

## 🔗 EPOCH 6 — Cross-Instance Trust Sovereignty

Multi-instance Docusaurus setups (e.g. `/docs/*` user area + `/developers/*`
contributor area) need legitimate cross-plugin links — but those links
look absolute (`/developers/foo`) and would normally trip `Z105 ABSOLUTE_PATH`.
v0.7.1 introduces a **declarative trust contract**:

```toml
# zenzic.toml — opt-in, empty by default
[link_validation]
absolute_path_allowlist = [
    "/docs/",
    "/developers/",
]
```

When an absolute link begins with an allowlisted prefix, the
`DocusaurusAdapter` treats it as a **Trusted Ghost Route** and the
validator silently bypasses Z105.

### Why this is configuration, not suppression

The orthogonality is doctrinal — codified in **ADR-0011 "Cross-Instance
Allowlist"**, section *Suppression vs Configuration*:

| Primitive | Scope | Form |
| :--- | :--- | :--- |
| `absolute_path_allowlist` | Repository-wide contract | Declarative config |
| `<!-- zenzic:ignore Z105 -->` | One specific line | Surgical local exception |

Using `<zenzic:ignore Z105>` for cross-plugin links is a **declared
anti-pattern**: it scatters routing knowledge across the corpus and
hides the contract.

### Hardened by Team-D destructive tests

Five contract tests guard the allowlist behaviour. Two of them are
adversarial: they prove the allowlist cannot silently degrade into a
catch-all when a contributor commits a typo, and document the
`startswith` semantics so neighbour-collisions (`/developers` matching
`/developers-internal/secret`) cannot sneak in unnoticed.

### Z108 deferred to v0.8.0 — by design

The natural follow-up — **Z108 `STALE_ALLOWLIST_ENTRY`**, which would
warn when an entry no longer matches any real link — is **explicitly
deferred** to v0.8.0 "Basalt". Implementing it inside the per-link
validator would violate Pillar 3 (Pure Functions) by introducing
shared mutable state across the scan. Its correct home is a separate
read-only `zenzic inspect config` command. Documented in the
[Technical Debt Ledger](https://zenzic.dev/developers/governance/technical-debt).

---

## 🌳 EPOCH 7a — Multi-Root Discovery (VSM Blindness Sealed)

For every release before v0.7.1 the VSM ingested **only** files under `docs_dir`.
Modern static-site generators routinely manage content trees that live outside `docs/` —
the textbook case is the Docusaurus `blog/` directory, materialised as live URLs at build
time. A pre-EPOCH-7a `zenzic check all --strict` would never see those files: broken
links inside (or pointing to) blog posts slipped past validation and only surfaced when
`docusaurus build` failed downstream. We call this failure mode **VSM Blindness**.

EPOCH 7a cures the blindness without compromising the three Pillars:

```python
# zenzic.core.adapters._base
@dataclass(frozen=True, slots=True)
class ContentRoot:
    path: Path        # absolute, e.g. <repo>/blog
    url_prefix: str   # e.g. 'blog' (or '' for root-served content)
    label: str        # diagnostic, e.g. 'docusaurus-blog'
```

Adapters opt in by implementing the optional
`get_extra_content_roots(repo_root) -> list[ContentRoot]` method. The Core discovers it
via `hasattr()` — the same convention already used by `get_locale_source_roots` — so
adapters that have nothing to declare need no stub. **The addition is non-breaking** for
third-party adapters built against the v0.7.1 Protocol.

### Four pipeline stages cooperate

1. **Discovery** — `iter_extra_content_markdown_sources` walks each root with
   `walk_files` (same `os.walk` engine, same `LayeredExclusionManager`) and yields
   `(abs_path, logical_rel)` pairs where `logical_rel` carries the URL prefix as its
   first segment.
2. **VSM** — `build_vsm` resolves every file's logical `rel` from `docs_root` *or* a
   matched extra root, then dispatches to the adapter's `get_route_info(rel)`.
3. **Validator** — the link checker loads extra-root files into `md_contents`, extends
   `_allowed_roots` so cross-tree relative links resolve under the Shield, and feeds
   the prefixed `rel` into "Did you mean?" suggestions.
4. **Scanner** — `find_unused_assets` (Z903) and `find_placeholders` iterate extra roots
   when collecting reference sets, so an asset cited only from a blog post is no longer
   reported as unused.

### Auto-discovery without `subprocess`

The Docusaurus adapter detects the blog plugin in two passes, both pure parsing:

1. Static regex parse of `docusaurus.config.{ts,js,mjs,cjs}` for a
   `blog: { path, routeBasePath }` block (or a sentinel `blog: false` to opt out).
2. Convention fallback: when the config does not pin the blog plugin and `<repo>/blog`
   exists on disk, assume the default plugin layout (`path = 'blog'`,
   `routeBasePath = 'blog'`).

**No Node.js process is ever spawned** — the config is read as data, not executed as
code. Pillar 2 (Engine Sovereignty) is preserved.

### Traceability invariant

A new contract test (`tests/test_docusaurus_blog_vsm.py::TestEpoch7aReverseMapping`)
asserts that every blog `Route.source` resolves back to a real file on disk:

```python
for route in blog_routes:
    assert route.source.startswith("blog/")
    assert (repo_root / route.source).is_file()
```

This locks the contract that EPOCH 7b virtual routes (tags, pagination, authors) will
inherit: a route with no physical origin would be a validator screaming `error` without
ever saying `where`.

### Engine support matrix

| Engine            | Implements `get_extra_content_roots` | Status                                                                |
|-------------------|--------------------------------------|------------------------------------------------------------------------|
| Docusaurus        | Yes                                  | Auto-discovers `blog/` from config or convention.                      |
| MkDocs (Material) | No                                   | Opt-in deferred until `material/blog` plugin enters the v0.7 scope.    |
| Zensical          | No                                   | Architecture is identical — enabled when an out-of-tree plugin ships.  |
| Standalone        | No                                   | No plugins; `docs_root` is the entire content surface.                 |

### Industry-grade compliance

- **Zero `rglob`**: every walk uses `walk_files` (deterministic `os.walk` with
  in-place exclusion pruning). The Determinism Invariant from the Quartz Era is
  preserved across the new content surface.
- **Zero subprocess**: no Node.js execution; the Docusaurus config is parsed as data.
- **Non-breaking**: the `hasattr()` opt-in pattern means existing adapters need no
  changes.
- **Seven new regression tests** lock the four invariants (discovery, VSM ingestion,
  reverse-mapping traceability, validator catches broken links) and ship green.

---

## 🌿 EPOCH 7a.1 — Zero-Config Sovereignty (`absolute_path_allowlist` Purged)

EPOCH 7a.1 extends the Zero-Config invariant to one of v0.7.1's last residues of
user-side coupling: the `[link_validation].absolute_path_allowlist` block.
Multi-instance Docusaurus sites (one `@docusaurus/plugin-content-docs`
instance per top-level URL prefix — e.g. `/docs/` for the user manual and
`/developers/` for the developer area) used to require the user to copy every
prefix into `zenzic.toml` so Z105 `ABSOLUTE_PATH` would not flag legitimate
cross-plugin links. That was a Zero-Config violation: Zenzic was forcing the
user to duplicate Docusaurus routing it could read for itself.

### What changes

- A new Protocol method `BaseAdapter.get_absolute_url_prefixes(repo_root) ->
  frozenset[str]` returns the absolute URL prefixes the engine owns at the
  current site. The validator queries the adapter via `hasattr()` (mirroring
  EPOCH 7a's `get_extra_content_roots` pattern) and bypasses Z105 for any
  internal absolute URL whose path starts with one of the discovered prefixes.
- `DocusaurusAdapter` implements the method with two pure-Python passes that
  honour Zero Subprocess:
  1. **Static parse** — a regex over `docusaurus.config.{ts,js,mjs,cjs}` walks
     every `@docusaurus/plugin-content-docs` tuple in the `plugins:` array and
     harvests its `routeBasePath`. Combined with the docs-plugin
     `routeBasePath` from the preset (already parsed for Multi-Root Discovery)
     and the EPOCH 7a blog `routeBasePath`, this yields the full set of
     project-owned prefixes.
  2. **Filesystem heuristic fallback** — when the config is dynamic
     (`module.exports = async () => …` etc.) and static parsing returns nothing,
     Zenzic walks `i18n/<locale>/docusaurus-plugin-content-docs-<id>/` and pairs
     each plugin instance with `<repo>/<id>/` if the directory exists. This
     matches the actual `zenzic-doc` layout and fires deterministically without
     ever launching Node.js.
- `LinkValidationConfig` and the `link_validation` field on `ZenzicConfig` are
  **removed in full** — no compat shim, no deprecation alias. Configurations
  that still declare `[link_validation]` will fail TOML validation. The
  industry-grade rule applies: breaking changes are always permitted.

### CEO Directive — Asset and Directory Cemeteries

The same audit revealed two more Zero-Config violations in `zenzic/zenzic.toml`:

- **`excluded_assets` boilerplate** — `*.toml`, `*.lock`, `*.yaml`, `*.json`,
  `LICENSE`, `NOTICE`, `Makefile`, `justfile`, `Dockerfile`, etc. were declared
  per-repo. Promoted to Layer 1 (`SYSTEM_EXCLUDED_FILE_NAMES` /
  `SYSTEM_EXCLUDED_FILE_PATTERNS`); user TOMLs no longer need them.
- **`excluded_dirs` boilerplate** — universal build directories (`build`,
  `dist`, `temp`, `tmp`, `mutants`) were declared per-repo. Promoted to
  `SYSTEM_EXCLUDED_DIRS`; only repo-specific entries (`src`, `tests`, `scripts`,
  `examples`, `assets`, `LICENSES`, `.redteam`) remain in `zenzic/zenzic.toml`.
- **Stale ghost paths** — `docs/configuration/*.md` and `docs/adr/*.md` were
  removed from `excluded_build_artifacts`; the directories had been estirpated
  in earlier EPOCHs and the entries were dead.

### Result

- `zenzic-doc/zenzic.toml`: 9 lines lighter (`[link_validation]` block + 3-line
  `excluded_assets`). The Docusaurus engine context is now *purely* engine
  context.
- `zenzic/zenzic.toml`: 28 lines lighter (asset cemetery + dir cemetery + stale
  paths purged). The standalone repo is back to the minimum viable
  configuration.
- `1433 / 1433` Core tests green. `zenzic check all` on `zenzic-doc` returns
  zero Z105 findings — the discovered prefixes do their job in production.

---

## 🚀 The Big Three

### 1. Sovereign Root Protocol

`zenzic check all /path/to/other-repo` now follows the **target's** configuration, not
the caller's working directory. Zenzic loads `zenzic.toml` from the target root and
resolves all paths relative to it. Every `check`, `score`, `diff`, and `init` command
accepts an optional `PATH` argument with sovereign semantics.

**Why it matters:** Monorepos, CI pipelines, and Genesis Nomad workflows (`zenzic init
/path/to/new-project`) all work correctly without shell gymnastics.

### 2. Matrix Laboratory — 20-Act Interactive Showroom

```bash
uvx zenzic lab          # interactive menu
uvx zenzic lab 3        # single act
uvx zenzic lab 11-16    # Red/Blue Team Matrix
uvx zenzic lab all      # full tour
```

The Lab ships **20** documented acts across five thematic sections:

| Section | Acts | Focus |
| :--- | :---: | :--- |
| 🛡 OS & Environment Guardrails | 0–3 | Linting, Shield, clean run |
| 🔗 Structural & SEO Integrity | 4–6 | Single-file, custom dir, proxy |
| 🏢 Enterprise Adapters & Migration | 7–10 | MkDocs, Docusaurus, Zensical, Z404 |
| 🔴 Red/Blue Team Matrix | 11–16 | Attack/defense, obfuscated credentials, stress tests |
| 📊 Scoring Scenarios | 17–19 | Security override, category caps, Base64 shadow |

### 3. Agnostic Universalism — Z404 Infrastructure Guard

Broken favicon and logo references are now caught for **every engine** — MkDocs
(`theme.favicon`, `theme.logo`), Zensical (`[project].favicon`, `[project].logo`),
and Docusaurus (`themeConfig.navbar.logo`, `themeConfig.footer.logo`). A missing logo
is a broken first impression; Zenzic treats it as a blocking error.

### 4. Protocol Sovereignty + War Room Examples (D080+D081)

The Core is now 100% engine-agnostic. `validator.py` no longer hardcodes engine names —
engine-specific link-scheme bypasses are declared via `BaseAdapter.get_link_scheme_bypasses()`
and queried at runtime (Rule R21). The `examples/matrix/` directory ships the living proof:
identical red-team attack vectors (Z201, Z105, Z502, Z401) produce identical findings across
standalone, mkdocs, and zensical engines. The blue-team fixtures earn the Sentinel Seal on
all three. Zero asymmetries.

---

## 🔐 EPOCH 8 — Z204 Enterprise Privacy Gate (Sovereign Local Configuration)

**Sprint D100** is a hard break, not a migration path. `.zenzic.dev.toml` is gone.
`.zenzic.local.toml` is the only supported machine-local configuration file.

### Why Hard-Remove, Not Deprecate

D002 introduced `.zenzic.dev.toml` as an Environmental Privacy Gate. v0.6.1 was never
published to end users; v0.7.1 is Year Zero. There are no production deployments to protect.
A deprecation warning would add scanning overhead and imply a support contract that
does not exist. The Quartz Maturity standard admits no nostalgia.

### The EPOCH 8 Solution

| Layer | Component | Behaviour |
| :---- | :-------- | :-------- |
| **Shield** | `scan_line_for_forbidden_terms()` in `shield.py` | Scans every documentation line against `forbidden_patterns`; emits a `FORBIDDEN_TERM` signal on match |
| **Config** | `forbidden_patterns: list[str]` in `ZenzicConfig` | Declared in `zenzic.toml` or additively merged from `.zenzic.local.toml` at load time |
| **Local file** | `.zenzic.local.toml` | Machine-local, git-ignored sole authority for private patterns; auto-scaffolded by `zenzic init` |
| **Finding** | **Z204 FORBIDDEN_TERM** | Exit 2; SARIF level `error`; Privacy Gate category |

### Architectural Invariants Preserved

- **Zero Subprocess** — `_apply_local_toml()` uses pure Python `tomllib`; no shell calls.
- **Engine Sovereignty** — Z204 is a core Shield rule, not an engine-specific extension.
- **Additive Merge** — patterns from `.zenzic.local.toml` are appended to any patterns already
  declared in `zenzic.toml`; duplicates are removed; insertion order is preserved.
- **No Silent Failures** — a malformed `.zenzic.local.toml` is skipped gracefully (engine continues).

---

## 🛡️ Security

**[D100] Z204 FORBIDDEN_TERM — Brand Integrity Shield (Sprint D100):** Two-layer
Privacy Gate architecture seals sensitive project vocabulary at the Shield layer (Exit 2).
Patterns are declared in machine-local, git-ignored `.zenzic.local.toml`.
`.zenzic.dev.toml` is hard-removed: not scanned, not loaded, not acknowledged.
Zero Subprocess invariant preserved.

**Sealed 5 critical bypass vectors — including the S2 Red Team attack vector (Base64) — during AI-driven red-team audit.**

The Red/Blue Team Matrix (Acts 11–16) revealed and verified defences against:
deep `../` path traversal chains targeting OS system directories (Blood Sentinel — exit 3),
credential obfuscation via Base64 encoding, percent-encoding, and mixed-case normalization
(Shield — exit 2), Windows absolute path injection (`C:\`, UNC shares), and cross-line
credential splitting via the ZRT-007 lookback buffer.

**Base64 Speculative Decoder (v0.7.1 D095):** The Shield now decodes candidate Base64 tokens
and re-scans the decoded text. A GitHub PAT encoded as `Z2hwXzEyMzQ...` in frontmatter
triggers Z201 and exits 2. Attack vector S2 sealed.

**KL-002 portability fix:** `os.path.normcase` applied to the Blood Sentinel boundary check
so that mixed-case paths on APFS/NTFS no longer produce false-positive traversal findings.

**Known limitations:** The ReDoS canary (`_CANARY_STRINGS` / `_assert_regex_canary`) uses
`SIGALRM` and is a **no-op on Windows** — the 50 ms interrupt is not available on that
platform. Plugin authors on Windows operate without startup ReDoS validation in v0.7.1.
Deterministic enforcement via a process-based watchdog is planned for v0.8.0 "Basalt".

Full audit report: [Quartz Tribunal Audit](https://zenzic.dev/docs/explanation/audit-v070-quartz-siege)

**Multi-Root Shield:** Cross-locale relative links no longer trigger false-positive
`PATH_TRAVERSAL_SUSPICIOUS` while preserving detection of links that escape every
authorised root.

---

## 📋 What's New at a Glance

- **Z204 FORBIDDEN_TERM — Enterprise Privacy Gate (Sprint D100)**: Shield rule that triggers
  Exit 2 when a forbidden term appears in any documentation file. Configured exclusively via
  `.zenzic.local.toml` (machine-local, git-ignored). `.zenzic.dev.toml` is hard-removed.
- **Law of Contemporary Testimony** — code and documentation updated in the same commit;
  documentation that contradicts the code is classified as a bug.
- **`zenzic score [PATH]` and `zenzic diff [PATH]`** — full PATH sovereignty for scoring.
- **`--no-color` / `--force-color`** and `NO_COLOR`/`FORCE_COLOR` environment variables.
- **`--offline` mode** — flat URL resolution for USB/intranet deployments.
- **`--quiet` flag** — single-line summary for pre-commit and CI silent builders.
- **`--no-external` flag** — skips Pass 3 HTTP HEAD requests for air-gapped / offline environments.
  Shield (Z201) and Blood Sentinel (Z202/Z203) remain fully active regardless of this flag.
- **Z502 pointer precision** — `❱` arrow skips SPDX licence headers and frontmatter to
  point at the first actual prose word.
- **1,307 passing tests · 80.28%+ coverage.** REUSE 3.3 compliant. mypy strict. Zero untyped definitions.
- **`zenzic inspect capabilities`** now shows a third section: Engine-specific Link Bypasses — which engine uses which URI scheme bypass via `get_link_scheme_bypasses()` (Rule R21).
- **`zenzic score` at 100/100** displays the Sentinel Seal celebratory panel — the same panel as Lab Act 0.
- **Sibling Automation:** `noxfile.py` + `justfile` for `zenzic-doc` and `zenzic-action`; single-command version bump for the Action (`just bump 0.7.x`).
- **Engine Guide Parity:** `engines.mdx` (EN+IT) — Zensical Transparent Proxy elevated to first-class migration feature with bridge mapping table; Standalone expanded to full section with use-case guide and limitations; MkDocs route URL resolution documented.
- **Docusaurus Full-Spec — UX-Discoverability Law:** `DocusaurusAdapter.get_nav_paths()` is now
  a Multi-Source Harvester that aggregates **sidebar** (`sidebars.ts`/`.js`), **navbar**
  (`themeConfig.navbar.items`), and **footer** (`themeConfig.footer.links`) statically
  (pure Python, no Node.js). A file is `ORPHAN_BUT_EXISTING` only if absent from all three
  UI navigation surfaces. MCP audit confirmed: in Docusaurus, routing is file-system driven;
  navigation surfaces are UX-discoverability constructs. Core purity preserved — `validator.py`
  never references "navbar", "sidebar", or "footer". 1 260 passing tests.
- **Brand Integrity — Z905 BRAND_OBSOLESCENCE:** New `BrandObsolescenceRule` detects obsolete
  release codenames in documentation sources. Configured via `[project_metadata]` in `zenzic.toml`
  (`release_name`, `obsolete_names`, `obsolete_names_exclude_patterns`). `[HISTORICAL]` token
  suppresses intentional historical references at the line level.
- **Z107 CIRCULAR_ANCHOR:** Detects self-referential anchor links (`[text](#heading)` on the same page).
- **Z505 UNTAGGED_CODE_BLOCK:** Detects fenced code blocks with no language specifier.
  Implements the CommonMark closing-fence invariant — Docusaurus metadata info strings
  (e.g. `` ```python title="file.py" ``) are fully supported and never flagged.
- **1,307 passing tests · 80.28% coverage.**

---

## 📦 Install

```bash
# One-shot — no install required
uvx zenzic lab

# Project dependency (version-pinned)
uv add --dev zenzic
zenzic check all --strict
```

## 🔗 Resources

- **Documentation:** [zenzic.dev](https://zenzic.dev)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Full history:** [CHANGELOG.archive.md](CHANGELOG.archive.md)

---

Zenzic is developed by **PythonWoods**, based in Italy, and committed to the craft of
high-performance, deterministic Python engineering.
