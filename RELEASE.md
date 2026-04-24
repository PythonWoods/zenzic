<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# 🛡️ Zenzic v0.7.0 — Obsidian Maturity

## "Engine-Agnostic. Integrity-Complete. The True Safe Harbor."

We are proud to announce **Zenzic v0.7.0 "Obsidian Maturity"**. This is a **minor release**
that marks a definitive evolution of the contract between Zenzic and its users. The volume
of change — Diátaxis architecture, universal Zxxx finding codes, Agnostic Universalism, the
interactive Lab, the Standalone renaissance, and the Vanilla purge — is not a collection of
bug fixes. It is a new standard of precision.

**v0.6.1 is superseded.** v0.7.0 is the canonical reference for all deployments.

---

### 🔬 Codebase Parity & Platform Robustness Sprint (2026-04-24)

A forensic sprint driven by failures surfaced on the Windows and macOS CI legs and
by a documentation audit comparing every public claim against the actual codebase.
The codebase is the single source of truth — documentation that contradicts it is a bug.

#### Cross-Platform Asset Resolution

`resolve_asset()` in all three adapter modules used `Path.exists()` for fallback path
validation. On Windows (NTFS) and macOS (HFS+), `Path.exists()` is case-insensitive:
`Logo.png` passes even when the file on disk is `logo.png`. This produced false
"asset found" results that silently suppressed valid Z403/Z404 findings.

**Fix:** `case_sensitive_exists(path)` — a new helper in `_utils.py` that uses
`os.listdir(path.parent)` to obtain the actual stored filenames from the OS and
performs an exact membership test. No platform branching; `os.listdir()` always
returns real names on every OS.

#### Placeholder Scanner Accuracy

`check_placeholder_content()` counted words in the raw Markdown source. Files with
`{/* long MDX comment */}` headers — used for copyright notices and SPDX metadata —
inflated the word count above the `placeholder_max_words` threshold, hiding genuine
short-content pages from detection (`docs/community/license.mdx` was the forensic case).

**Fix:** `_visible_word_count(text)` strips YAML frontmatter, MDX block-comments
(`{/* … */}`), and HTML comments (`<!-- … -->`) before splitting. The scanner now
counts only prose visible to the reader.

#### Z000 Guard — TODO Removed

`_factory.py` carried `# TODO: Remove this migration guard in v0.7.0`. The guard
that raises `ConfigurationError` when `engine = "vanilla"` is not temporary — vanilla
was permanently removed in v0.6.1. The comment has been replaced with a permanent
explanation so no future maintainer mistakes it for technical debt to delete.

#### Documentation Audit — 5 DOC_ERRORs Corrected (zenzic-doc)

A full pass comparing every documentation claim against the codebase found five
categories of error, all classified as **DOC_ERROR** (wrong docs, correct code):

| Finding | Location | Correction |
|---|---|---|
| `VanillaAdapter` (13 occurrences) | architecture, engines, adapter guide, glossary, install, custom-rules, faqs, i18n mirrors | → `StandaloneAdapter` |
| `"code": "BROKEN_LINK"` | `cli.mdx`, `configure-ci-cd.mdx` (EN + IT) | → `"code": "Z104"` |
| Z000 described as a collectable finding | `finding-codes.mdx` (EN + IT) | → `ConfigurationError` exception, absent from `--format json` |
| ASCII box diagram | `checks.mdx` (EN + IT) | → Mermaid `flowchart LR` with ObsidianPalette colours |
| Incorrect message format in JSON examples | `cli.mdx`, `configure-ci-cd.mdx` (EN + IT) | → `"file:line: 'target' not found in docs"` |

#### Security — CVE-2026-3219 (pip polyglot archive)

`pip 26.0.1` is affected by CVE-2026-3219: concatenated tar + ZIP archives are treated
as ZIP regardless of filename, potentially installing the wrong files. No patched pip
release exists on PyPI. Zenzic is not at risk — `uv` handles all package management
and pip is present only as a transitive dependency of pip-audit. All packages are pinned
via `uv.lock`. Added `--ignore-vuln CVE-2026-3219` to `nox -s security` with a removal
reminder for when pip ships a fix.

---

### 🧬 Test Coverage & Mutation Testing Sprint (2026-04-24)

A targeted sprint to measure and strengthen the test suite using both line coverage
and mutation testing (`mutmut`). The output: 1 195 passing tests, a new `test_cache.py`
module from scratch, and targeted mutant-killing tests for three critical subsystems.

#### New Test Modules

- **`tests/test_cache.py`** — 29 tests covering the entire content-addressable cache
  (`cache.py`). Pure hash stability, `CacheManager` get/put/overwrite, hit-rate tracking,
  atomic save, parent-dir creation, corrupt-JSON resilience, and OSError cleanup.
- **`tests/test_reporter.py`** — 12 tests for `_read_snippet` and `_strip_prefix`.
  Exercises the `or`/`and` boundary that guards against empty files and invalid line
  numbers, context-window clamping, and prefix-stripping semantics.

#### Mutation Testing Results

Full `mutmut` run across `rules.py`, `shield.py`, and `reporter.py`. High-impact logic
mutants confirmed killed:

| Mutant class | Function | Representative mutation | Killed by |
|---|---|---|---|
| Boundary | `_obfuscate_secret` | `<= 8` → `< 8` | `TestObfuscateSecretMutantKill` |
| Logic inversion | `_to_canonical_url` | `and "…" in path` → `or` | `TestToCanonicalUrlMutantKill` |
| Strip substitution | `_normalize_line_for_shield` | MDX sub → `"XXXX"` | `TestNormalizeLineForShieldMutantKill` |
| String mutation | `_to_canonical_url` | `rstrip("/")` → `rstrip(None)` | `test_trailing_slash_is_stripped_*` |
| Index arithmetic | `_to_canonical_url` | `parts[:-1]` → `parts[:+1]` | `test_nested_index_removed` |

Remaining survivors are equivalent mutants: template string variations in
`SentinelReporter.render` output formatting and `encoding`/`errors` argument
mutations that Python's codec system normalises at runtime.

---

### 🚀 What Changed

#### 1. Z104 Proactive Suggestion Engine (New)

When Zenzic cannot find a linked file (`Z104 FILE_NOT_FOUND`), it now computes the closest
match from the in-memory VSM using `difflib.get_close_matches` and appends:

```text
💡 Did you mean: 'docs/guide/setup.mdx'?
```

No disk I/O in the hot path. If you mistype a filename, Zenzic takes you by the hand.

#### 2. Standalone Mode Truth Audit

Every description of **Standalone Mode** now explicitly declares its limits:

> Orphan detection (`Z402`) is disabled — there is no navigation contract.

What you DO get: full link validation (`Z101`/`Z104`), credential scanning (`Z201`),
path-traversal blocking (`Z202`), and directory-index integrity (`Z401`).

All example `zenzic.toml` files migrated from the legacy `engine = "vanilla"` to
`engine = "standalone"`.

#### 3. Engineering Ledger

The `## Design Philosophy` section in both `README.md` and `README.it.md` has been
replaced with an **Engineering Ledger** — three non-negotiable operational contracts
expressed as machine-verifiable evidence, not marketing prose:

| Contract | Evidence |
|----------|---------|
| Zero Assumptions | `mypy --strict` — zero untyped defs |
| Subprocess-Free | `ruff` rule banning `subprocess` |
| Deterministic Compliance | REUSE 3.x SPDX on every file |

#### 4. Sentinel Mesh Tightening

**Forensic finding:** The `excluded_external_urls` block contained `"https://zenzic.dev/"` —
a blanket prefix exclusion added when the site was not yet deployed. This meant ALL
documentation links in `README.md` were silently excluded from `--strict` validation,
even as the Diátaxis restructure had invalidated three of them.

**Fixed:**

- Removed the blanket `https://zenzic.dev/` exclusion.
- Corrected the three stale link targets in `README.md` and `README.it.md`:
  - `/docs/usage/badges/` → `/docs/how-to/add-badges/`
  - `/docs/guides/ci-cd/` → `/docs/how-to/configure-ci-cd/`
  - `/docs/internals/architecture-overview/` → `/docs/explanation/architecture/`
- Added `⚠ PERIMETER INVARIANT` comment in `zenzic.toml` documenting that
  `docs_dir = "."` is a safety invariant, not a convenience setting.

### 🛠️ Developer Notes

- **zenzic-doc README:** Node.js prerequisite corrected from 20 to 24. CI matrix
  wording updated to "Node 22 and 24". Stale i18n route `/docs/intro` removed.
- **Self-validation:** After all fixes, `zenzic check all` on the core repo exits 0.
  The Sentinel now bites its own hand correctly.

### Migration

No breaking changes. Upgrade with:

```bash
uv tool upgrade zenzic
# or
pip install --upgrade zenzic
```

---

### ⚗️ The Agnostic Universalism (Direttiva CEO 087)

A Safe Harbor that claims engine-agnosticism cannot document a core feature as if it
were exclusive to a single engine. **Z404 is now universal.**

#### 6. Z404 Extended to MkDocs and Zensical

`check_config_assets()` is now implemented for all three first-class engines:

| Engine | Config file | Fields checked | Resolved against |
|--------|-------------|----------------|-----------------|
| **Docusaurus** | `docusaurus.config.ts` | `favicon:`, `image:` (OG) | `static/` |
| **MkDocs** | `mkdocs.yml` | `theme.favicon`, `theme.logo` | `docs_dir/` |
| **Zensical** | `zensical.toml` | `[project].favicon`, `[project].logo` | `[project].docs_dir/` |

Icon names (e.g. `material/library`) are skipped via image-extension filter — no false positives.
`cli.py` now dispatches Z404 across all three engines. Lab Acts 9 and 10 demonstrate the
detection live.

```text
warning  [Z404]  mkdocs.yml
  theme.favicon: 'assets/images/missing-favicon.png'
  💡 Expected at: docs/assets/images/missing-favicon.png
```

```text
warning  [Z404]  zensical.toml
  [project].logo: 'assets/images/missing-logo.png'
  💡 Expected at: docs/assets/images/missing-logo.png
```

#### 7. Lab Acts 9 & 10 — MkDocs Favicon Guard / Zensical Logo Guard

Two new Lab acts and example fixtures (`examples/mkdocs-z404/`, `examples/zensical-z404/`)
provide a live demonstration of Z404 across MkDocs and Zensical. Run them with:

```bash
zenzic lab 9   # Z404 on MkDocs theme.favicon + theme.logo
zenzic lab 10  # Z404 on [project].favicon + [project].logo
```

Act validator updated to `0–10`.

#### 8. Z404 Documentation Rewritten as Agnostic

`finding-codes.mdx` (EN + IT) Z404 section now covers all three engines with per-engine
field tables, per-engine remediation snippets, and a unified Adapter Coverage note.

---

### 🪞 The Obsidian Mirror Pass (Direttive 082–086)

The second wave of v0.7.0 work closes every gap identified during the Obsidian Mirror audit: the Sentinel now checks its own infrastructure, the Lab now looks exactly like
production, and the documentation portal is fully aligned.

#### 5. Z404 CONFIG_ASSET_MISSING — Docusaurus Bootstrap (Direttiva 085)

Zenzic can detect the same class of fault that D084 found manually:
a `favicon:` or `image:` path declared in `docusaurus.config.ts` that does not
exist inside `static/`. This was the initial Docusaurus-only implementation,
later extended to MkDocs and Zensical in Direttiva 087 (see above).

#### 6. Lab Obsidian Seal

`zenzic lab <N>` output is now **identical** to `zenzic check all`:
the same `SentinelReporter.render()` pipeline, the same indigo panels, the same
Sentinel Palette colours. Every act now closes with a dedicated **Obsidian Seal**
panel showing:

- Files scanned (docs + assets)
- Elapsed time and **throughput in files/s**
- Per-act pass/fail verdict with branding-consistent colours

Full-run summaries (all acts) aggregate throughput across the entire showcase run.

#### 7. Documentation Portal — Infrastructure Hardening

- **Favicon 404 fixed:** `favicon: 'img/favicon.ico'` corrected to
  `'assets/favicon/png/zenzic-icon-32.png'`. Z404 now catches this automatically.
- **OG meta completeness:** `twitter:image:alt`, `og:image:width` (1200),
  `og:image:height` (630) added to `docusaurus.config.ts`.
- **Z404 documented:** `finding-codes.mdx` (EN + IT) contains the full
  `Config Asset Integrity` reference section. Capability Matrix in both READMEs
  updated with the new row.
- **Dependencies bumped:** tailwindcss 4.2.4 · autoprefixer 10.5.0 ·
  postcss 8.5.10 · typescript 6.0.3. Build confirmed green.
- **Dependabot extended:** GitHub Actions ecosystem added; Docusaurus and React
  grouped to reduce PR noise.
- **Bump script:** `scripts/bump-version.sh` + `just bump` automate all six
  hardcoded version strings in the portal on every release.

---

### 🛡️ Guardians Security Audit — Pre-Release Shield Hardening

The final sprint before the v0.7.0 tag was a forensic audit of `shield.py` conducted
by the Guardians team. The audit revealed three hardening techniques and one credential
family that were implemented in code but invisible to users in the documentation.

**What was found:**

| Finding | Status before audit | Status after |
|---------|--------------------|----|
| ZRT-006: Unicode Cf character stripping | ✅ In code since v0.6.1 | ✅ Documented (EN + IT) |
| ZRT-006: HTML entity decode (`html.unescape`) | ✅ In code since v0.6.1 | ✅ Documented (EN + IT) |
| ZRT-007: Comment interleaving strip | ✅ In code since v0.6.1 | ✅ Documented (EN + IT) |
| ZRT-007: 1-line lookback buffer (`scan_lines_with_lookback`) | ✅ In code since v0.6.1 | ✅ Documented (EN + IT) |
| `gitlab-pat` — 9th credential family (`glpat-[A-Za-z0-9\-_]{20,}`) | ✅ In code | ✅ Documented + README updated |

**Impact:** `architecture.mdx` Pre-scan Normalizer table expanded from 3 rows to 6 rows.
Pattern Families table updated from 8 to 9 entries. Hardening section documents the
80-char tail-head join that catches secrets split across line boundaries.

**CLI Refactor:** `cli.py` (1 968 lines) de-monolitized into the `cli/` package with
five responsibility-scoped modules and a Visual State Guardian law enforced via
`get_ui()` and `get_console()` in `_shared.py`. The `main.py` import contract is
unchanged — this is a zero-impact internal restructure.

**Releasing v0.7.0 without this audit would have left five security features
undocumented.** The Guardians' work is the final seal of the Porto Sicuro.

---

### 🌐 Bilingual Integrity Seal — Multi-Root Safe Harbor (Direttive 123–128)

The i18n blind spot that v0.7.0 closes is architectural, not cosmetic.

When a translator working in `i18n/it/` updates `[link text](#contesto)` but leaves the
heading as `{#context}`, no prior version of Zenzic raised an error.
`validate_same_page_anchors` defaults to `False`, and the locale file lived outside
`docs_root` — invisible to both the anchor checker and the Shield.

#### What changed

**Multi-Root Shield** (`InMemoryPathResolver` — `allowed_roots`)
Cross-locale relative links (`i18n/it/intro.md` → `i18n/it/guide.md`) no longer trigger
false-positive `PATH_TRAVERSAL_SUSPICIOUS`. The resolver now holds a tuple of
`(root_str, root_prefix)` pairs — one per authorised root — and the Shield performs
an `any()` prefix check in the hot path with zero `Path` allocations.
Security invariant preserved: a link to `../../../../etc/passwd` still hits
`PATH_TRAVERSAL_SUSPICIOUS` because the target falls outside every authorised root.

**Mandatory i18n Anchor Integrity**
Files inside `i18n/` locale directories are always validated for same-page anchors,
regardless of `validate_same_page_anchors`. The `locale_file_set: frozenset[Path]`
tracks which files came from locale roots; the anchor check fires when
`config.validate_same_page_anchors or md_file in locale_file_set`.

**`@site/` Alias Extended to `repo_root`**
`known_assets` now scans `repo_root` instead of only `docs_root`, so that
`@site/static/logo.png` referenced inside a locale file resolves correctly against
`static/` at the repository root.

**`zenzic init` Docusaurus Template**
`zenzic init` detects `docusaurus.config.ts` / `docusaurus.config.js` and emits:

```toml
[build_context]
engine = "docusaurus"
# locales = []  # e.g. ["it", "fr"]
# Zenzic v0.7.0+ automatically authorizes i18n/ locale roots.
# No extra configuration is needed for standard translation folders.
```

**Guardian Coverage**
`tests/guardians/test_i18n_path_integrity.py` defines four invariants (INT-001 through
INT-004) across eleven test cases. The suite runs on every push to `main` and
`release/**` — it is not a unit test, it is a contractual guarantee.

| Invariant | Guarantee |
|-----------|-----------|
| INT-001 | Cross-locale relative links → PASS |
| INT-002 | Traversal to OS system path from locale file → PATH_TRAVERSAL_SUSPICIOUS |
| INT-003 | Same-page anchor mismatch in locale file → ANCHOR_MISSING (always) |
| INT-004 | `@site/static/` assets resolve correctly from locale files |

---

### ⚓ Stability Declaration

**v0.7.0 is the canonical stable reference for the Obsidian Maturity sprint.**
v0.6.1 is superseded and should not be used in new deployments.

Every promise made in v0.6.1 has been audited, corrected, and verified end-to-end:

| Gate | Result |
|------|--------|
| `zenzic check all` on core repo | ✅ Exit 0, strict mode |
| `ruff check` + `mypy --strict` | ✅ Zero warnings |
| Test suite (1124/1127) | ✅ 3 known timing flakies isolated |
| `npm run build` (EN + IT) | ✅ Zero broken-link errors |

---

### 🇮🇹 Engineered with Precision

Zenzic is developed by **PythonWoods**, based in Italy, and committed to the craft of
high-performance, deterministic Python engineering.

**For the documentation portal release, see [zenzic-doc v0.7.0](https://github.com/PythonWoods/zenzic-doc/blob/main/RELEASE.md).**

[**Read the Full Documentation →**](https://zenzic.dev)

## "Precision, Security, and the new Standalone Standard."

We are proud to announce the stable release of **Zenzic v0.6.1 "Obsidian Glass"**. This version marks a major milestone in our mission to provide the most resilient, engine-agnostic documentation integrity suite for the modern engineering stack.

Documentation should be portable, secure, and verifiable regardless of the build engine you choose. With *Obsidian Glass*, Zenzic breaks the final chains of engine dependency — and speaks a professional language that enterprises can audit.

### 🚀 Key Highlights

#### 1. Standalone Engine — A New Identity

We replaced the informal "Vanilla" mode with a robust **Standalone Engine**, ensuring Zenzic is the perfect companion even for pure Markdown folders that have no build framework at all. The `StandaloneAdapter` is now the canonical engine for framework-free projects, and `zenzic init` writes `engine = "standalone"` automatically when no framework configuration is detected.

> *"We replaced the 'Vanilla' mode with a robust Standalone Engine, ensuring Zenzic is the perfect companion even for pure Markdown folders."*

**Breaking change:** `engine = "vanilla"` in any `zenzic.toml` now raises `ConfigurationError [Z000]`. Update to `engine = "standalone"`.

#### 2. Zenzic Finding Codes (Zxxx)

Introducing **Zenzic Finding Codes**: every diagnostic message now carries a unique `Zxxx` identifier, giving the Sentinel a professional language for enterprise-grade reporting and future tooling integrations.

> *"Introducing Zenzic Finding Codes (Zxxx): giving our Sentinel a professional language for enterprise-grade reporting."*

| Code | Meaning |
|------|---------|
| Z101 | LINK_BROKEN |
| Z201 | SHIELD_SECRET |
| Z401 | MISSING_DIRECTORY_INDEX |
| Z402 | ORPHAN_PAGE |

Full registry: `src/zenzic/core/codes.py`.

#### 3. Interactive Lab (`zenzic lab`)

The `zenzic lab` command is now **menu-driven**. Run it without arguments to see all nine acts and choose what to explore. Run `zenzic lab <N>` to dive straight into a specific scenario.

#### 4. Zensical Transparent Proxy (Legacy Bridge)

Migrating from MkDocs to Zensical? Do it one step at a time. Zenzic now includes a transparent bridge that allows the **Zensical engine** to understand your legacy `mkdocs.yml` structure. No configuration changes required — Zenzic identifies your project and bridges the gap automatically.

#### 2. Docusaurus v3 Multi-Versioning

Zenzic is now a first-class citizen for large-scale Docusaurus projects. We’ve implemented native support for `versions.json` and the `versioned_docs/` directory. Your versioned routes are now automatically tracked in the **Virtual Site Map (VSM)**, ensuring that links to older documentation are validated with the same rigor as your latest release.

#### 3. Global Offline Mode (`--offline`)

Distributed documentation on USB drives? Local intranets without directory-index support? The new `--offline` flag forces all adapters to resolve Markdown sources to flat `.html` files (e.g., `intro.md` → `/intro.html`). Ensure your documentation remains navigable even in air-gapped environments.

#### 4. @site/ Alias Resolution

For Docusaurus users, we’ve added support for the `@site/` path alias. Zenzic now correctly resolves project-relative links like `[logo](@site/static/img/logo.png)` without requiring complex exclusion rules.

### 🛠️ Migration & Call to Action

If you are currently using MkDocs and considering a move to a more modern, TOML-based or MDX-powered architecture, **Zenzic v0.6.1 is your safety net**.

1. Install Zenzic: `uv tool install zenzic`
2. Run `zenzic check all` on your existing MkDocs project.
3. Switch your engine to `zensical` or `docusaurus` and watch Zenzic validate the migration in real-time.

**If you used `engine = "vanilla"`:** update your `zenzic.toml` to `engine = "standalone"` before upgrading.

---

### 🚀 Zenzic goes Enterprise (Direttive CEO 092–095)

Zenzic v0.7.0 is not just "more accurate" — it is now a **first-class CI infrastructure component**.

#### SARIF Export: Into the Security Dashboard

Every `check` command now supports `--format sarif`. Upload the output to GitHub Code Scanning and
your documentation errors appear **inline in Pull Request diffs** and in the **Security tab** —
no log parsing, no custom scripts, no manual triage.

```bash
zenzic check all --format sarif > zenzic-results.sarif
```

The SARIF report is valid against [SchemaStore 2.1.0](https://json.schemastore.org/sarif-2.1.0.json),
includes named rule entries for every Z-code, and carries `security-severity` scores (`9.5` for
credential breaches, `9.0` for path-traversal incidents) for GitHub Advanced Security prioritization.

#### Official GitHub Action

Stop writing manual `uvx` steps. One block is all you need:

```yaml
- name: 🛡️ Zenzic Documentation Quality Gate
  uses: PythonWoods/zenzic-action@v1
  with:
    format: sarif
    upload-sarif: "true"
```

The action installs Zenzic, runs `check all`, writes `zenzic-results.sarif`, and uploads to Code
Scanning automatically. Add `permissions: security-events: write` to the job and the rest is handled.

#### Cross-Platform Validation Matrix

Every commit now runs on Ubuntu, Windows, and macOS across Python 3.11, 3.12, and 3.13.
Nine jobs. `fail-fast: false`. Pure Python is claimed — now it is proven.

---

### 🇮🇹 Engineered with Precision

Zenzic is developed by **PythonWoods**, based in Italy, and committed to the craft of high-performance, deterministic Python engineering.

[**Read the Full Documentation →**](https://zenzic.dev)
