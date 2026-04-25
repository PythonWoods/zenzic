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

### 🛡️ Sentinel Integrity & Knowledge Codification Sprint (2026-04-25)

#### Blood Sentinel Sovereign Sandbox (Direttiva CEO 043)

`zenzic check all ../external-docs` previously raised **Exit 3** (Blood Sentinel — path
traversal) when the explicit target lived outside the CWD repository root. This was a
false positive: the F4-1 guard could not distinguish a user-supplied external path from
an adversarial path injected via a malicious config file.

**The fix: the explicit target becomes the sovereign sandbox.** If the CLI receives a
`PATH` argument and `docs_root` falls outside `repo_root`, the engine reassigns
`repo_root = docs_root`. Blood Sentinel then guards escapes *from* that target — which
is exactly its purpose. The flag is gone; the logic is correct.

A companion fix hoists the Zenzic banner to the start of `check_all`, guarded by format
mode — so every exit, including fatal ones, announces itself correctly.

Integration test `test_check_all_external_docs_root_not_blocked_by_sentinel` locks this
behaviour permanently.

#### Obsidian Ledger — The Knowledge Trinity (Direttive CEO 046–047)

The three repository agent instruction files (`.github/copilot-instructions.md`) have
been completely rewritten into the **Obsidian Ledger** schema:

> `[MANIFESTO] → [POLICIES] → [ARCHITECTURE] → [ADR] → [CHRONICLES] → [SPRINT LOG]`

Key corrections applied to the `zenzic` ledger: the CLI is a *package* (`cli/`), not a
single file; the UI module lives in `core/ui.py`; the Lab is in `cli/_lab.py`; there are
11 Acts (0–10); Z504 `QUALITY_REGRESSION` is documented for the first time. The
`_factory.py` Z000 guard is marked permanent — not a TODO.

`zenzic-action` receives its first-ever agent instruction file. The Knowledge Trinity is
complete: Core + Docs + Action all have authoritative Obsidian Ledger instructions.

---

### 🧠 Obsidian Memory Law & Precision Polish (Direttive CEO 048–049)

#### The Custodian's Contract — Resolving the Memory Paradox (D049)

An AI agent has no persistent memory between sessions. Left unaddressed, this means
every sprint closure depends on the agent remembering its own obligations — a paradox.
The **Obsidian Memory Law** resolves it structurally.

Each of the three Obsidian Ledger files now opens with a **`[CLOSING PROTOCOL]`** —
a mandatory, per-repo sprint-closure checklist positioned *before* `[POLICIES]` so it
cannot be skimmed past. Skipping any step is classified as a **Class 1 violation
(Technical Debt)**. The Memory Law in `[POLICIES]` is elevated to "The Custodian's
Contract": this file is the agent's only persistent memory, and a sprint is not closed
until every checkbox is ticked. The paradox is not solved by memory — it is solved by
*protocol*.

#### Four Precision Bug Fixes (D048)

A precision audit of the reporter and snippet validator surfaces four bugs, all fixed
with regression tests:

**Z502 — Pointer targets frontmatter, not content.** Short-content findings reported
`line_no=1`, pointing at the YAML frontmatter `---` delimiter. A new `_first_content_line()`
helper uses `_FRONTMATTER_RE` to locate the first post-frontmatter line; the pointer now
targets actual content.

**Z503 — YAML errors report snippet-relative line, not absolute file line.** The YAML
exception handler always emitted `fence_line + 1`, discarding the parser's own
`problem_mark.line` offset. A syntax error on snippet line 3 at file line 183 was
reported as line 181. The handler now reads `exc.problem_mark.line` (0-indexed) and
adds it correctly to the fence offset.

**Z105/Z503 — Caret misalignment on long source lines.** The `_render_snippet()`
function rendered full source lines and computed carets based on raw string length,
ignoring terminal wrapping. A caret at column 80 on a 200-character line appeared on
the wrong visual row after wrapping. The fix: lines are truncated to
`terminal_width − gutter_overhead` characters with a `…` suffix; carets are suppressed
when `col_start` falls in the truncated (invisible) region.

**Z503 — False positive for multi-document YAML snippets.** `yaml.safe_load()` raises
`ComposerError: expected a single document` when a snippet contains `---` (a valid
YAML document separator, common in Docusaurus frontmatter examples). The fix replaces
`safe_load()` with `list(yaml.safe_load_all())`, which correctly handles
multi-document streams.

---

### 🛡️ The Intelligent Perimeter (Direttiva CEO 050)

A tool that flags its own configuration inputs as quality issues is not a Safe Harbor — it is a
noise generator. **D050** closes the last gap in the exclusion architecture.

#### Zero-Noise Asset Scanning

When `docs_root` equals the project root, Zenzic previously emitted spurious Z903 (Unused Asset)
warnings on `docusaurus.config.ts`, `package.json`, `pyproject.toml`, and other toolchain files.
These files are the inputs Zenzic reads to operate. The fix is architectural, not cosmetic.

**Level 1a — Global Infrastructure Guardrails:** A new `SYSTEM_EXCLUDED_FILE_NAMES` frozenset
and `SYSTEM_EXCLUDED_FILE_PATTERNS` tuple in `models/config.py` enumerate universal toolchain
files that are never documentation content. Like `SYSTEM_EXCLUDED_DIRS`, these are immutable
system guardrails — no user config or CLI flag can override them.

**Level 1b — Adapter-Driven Metadata:** Each adapter now declares which engine config files it
consumes via `BaseAdapter.get_metadata_files()`. Docusaurus shields `docusaurus.config.ts`,
`sidebars.ts`, and `_category_.json`. MkDocs shields `mkdocs.yml`. Zensical shields
`zensical.toml`. `LayeredExclusionManager` stores adapter metadata files at construction time
and enforces them in `should_exclude_file()`. `find_unused_assets()` applies both layers before
building the asset set.

The result: zero Z903 warnings on infrastructure. The user's `zenzic.toml` stays clean,
focused only on *their* business exclusions — not on the scaffolding of the tool itself.

---

### 📖 Documentation as an Invariant (Direttiva CEO 051)

A behavioral change that is not reflected in the documentation is a ghost commit — it alters
reality without updating the map. **D051** codifies this as an iron law and then immediately
applies it to three files whose contents had drifted from the v0.7.0 codebase.

#### The Obsidian Testimony Law

A new **Documentation Law — The Obsidian Testimony** has been added to `[POLICIES]` in all
three repository Obsidian Ledgers (`zenzic`, `zenzic-doc`, `zenzic-action`). It is not a
guideline — it is a mandatory trigger system:

| What changed in code | What must be updated |
|----------------------|----------------------|
| I/O, config options, or exclusion logic | `reference/configuration.mdx` (EN + IT) |
| UI output, CLI flags, or module structure | `explanation/architecture.mdx` (EN + IT) |
| A `Zxxx` finding (threshold, message, line accuracy) | `reference/finding-codes.mdx` (EN + IT) |
| Adapter discovery or engine config handling | `how-to/configure-adapter.mdx` (EN + IT) |

The `[CLOSING PROTOCOL]` Step 3 has been renamed from "Staleness Audit" to
**"Staleness & Testimony Audit"** in all three ledgers, with per-repo trigger checklists.

#### Three Documentation Pages Updated (zenzic-doc)

**`reference/finding-codes.mdx` (EN + IT):**

- **Z502 SHORT_CONTENT:** Technical Context now explicitly documents that the word count is
  purely *semantic* — YAML frontmatter, MDX comments (`{/* */}`), and HTML comments
  (`<!-- -->`) are excluded. The 50-word threshold applies only to rendered prose.
- **Z503 SNIPPET_ERROR:** Technical Context now documents that the reported line number is
  *absolute* — relative to the source file, not to the start of the snippet. This enables
  immediate `file:line` navigation without mental arithmetic.

**`reference/configuration.mdx` (EN + IT):**

- New **System Guardrails (Level 1 Exclusions)** section documents the full list of files
  automatically shielded by L1a (universal infrastructure) and L1b (adapter-declared engine
  configs). Users no longer need to guess what is already protected.
- The `excluded_assets` section updated: the `**/_category_.json` pattern is no longer
  required for Docusaurus projects (Level 1b guardrail in `DocusaurusAdapter`). Existing
  entries remain valid and are silently deduplicated.

**`how-to/configure-adapter.mdx` (EN + IT):**

- New tip box after the adapter discovery table: engine configuration files consumed by each
  adapter are automatically excluded from Z903. No manual `excluded_assets` entry required.

---

### 🧭 The Sovereign Root Fix (Direttiva CEO 052)

Zenzic is designed to be invoked from anywhere — from CI runners, from editor integrations, from
scripts that scan multiple repositories in sequence. **D052** seals a long-standing assumption that
silently broke the tool when you aimed it outside your current working directory.

#### The Bug: Context Hijacking

Running `zenzic check all /path/to/other-repo` from inside repo A would load **A's** `zenzic.toml`
instead of the target's. The engine adapter, `docs_dir`, strict mode, and exclusion rules all came
from the wrong project. In the worst case, A's `docs_dir = "docs"` would mismatch B's actual
documentation directory — producing false positives, missed errors, or both.

A secondary bug compounded the problem: when the explicit path equalled the target's repository root,
`_apply_target()` would override `docs_dir` to `"."` — scanning the entire project directory
(including `blog/`, `scripts/`, `node_modules/`) instead of the configured documentation folder.

#### The Fix: ADR-009 Path Sovereignty

> **"The configuration follows the target, not the caller."**

`find_repo_root()` now accepts a `search_from` parameter. When an explicit `PATH` is given to
`zenzic check all`, the function searches upward from that path — not from `os.getcwd()`. The
calling directory is irrelevant. The target's `zenzic.toml` is loaded, its engine adapter is
activated, its `docs_dir` is respected.

The `_apply_target()` sovereign root guard handles the second bug: when the explicit target is the
project root itself, `docs_dir` is preserved from the loaded configuration rather than overridden.

Nine regression tests in `tests/test_remote_context.py` ("The Stranger" suite) verify that
configuration isolation holds across all scenarios.

---

### 🔒 The Portability Invariant (Direttiva CEO 053)

D053 is a two-part enforcement action: confirming an existing guarantee and fixing a violation of
Zenzic's own rules that was introduced in the previous sprint.

#### Z105 is Already a Hard Gate

Investigation of `validator.py` confirmed that Z105 (Absolute Path) fires unconditionally — before
any filesystem check. The `continue` on line 804 short-circuits the validation pipeline immediately
when a link starts with `/`, regardless of whether the target file exists on disk. The `@site/`
Docusaurus alias is handled separately (it starts with `@`, not `/`) and is correctly exempted.

**Rule R14** has been codified in `[POLICIES]` to make this invariant permanent:
> *Absolute links (starting with `/`) are hard errors (Z105) unconditionally — even if the target
> file exists on disk and is reachable locally.*

#### D051 Self-Audit: Two Absolute Links Fixed

The D051 documentation sprint introduced two absolute links in `configure-adapter.mdx` (EN and IT):

```text
[System Guardrails](/docs/reference/configuration#system-guardrails)   ← Z105 violation
```

These were valid Docusaurus navigation links, but they violate Z105 in Zenzic's own internal scan.
Both have been replaced with relative MDX paths:

```text
[System Guardrails](../reference/configuration.mdx#system-guardrails)  ← correct
```

A dedicated regression test verifies that Z105 fires on an absolute link even when the physical
target file exists: `test_z105_fires_even_when_target_file_exists_on_disk`.

---

### 🔬 The Strict Perimeter Law (Direttiva CEO 054)

This sprint began with a CEo-level incident report: a Z104 error appeared on a link that was
passing cleanly during internal scans. The investigation produced a precise forensic record and
closed two outstanding issues.

#### The Incident: Z104 on a Valid Link

The link `../assets/brand/svg/zenzic-badge-shield.svg` in `docs/community/brand-kit.mdx` was
flagged as Z104 (file not found) when Zenzic was run from outside the zenzic-doc repository —
but passed silently when run from inside. This appeared to confirm the CEO's "Permissive
Perimeter" theory.

**Forensic conclusion:** The link is structurally correct. The file exists at
`docs/assets/brand/svg/zenzic-badge-shield.svg` — inside `docs_root`. The Shield resolver
already enforces scope integrity unconditionally (PathTraversal Z202 fires for any link that
escapes the perimeter). The Z104 was a CEO-052 artifact: running from a sibling directory before
the sovereign root fix caused the wrong `known_assets` index to be built.

After CEO-052 fix: `find_repo_root(search_from=zenzic-doc)` → correct repo root → correct
asset index → no Z104. Both internal and external scans now produce identical Obsidian Seal
output.

#### BUG-011: The Inverted Ghost Commit

The investigation surfaced a second, more subtle issue. The documentation for `excluded_dirs`
listed `"assets"` as part of the default:

```text
["includes", "assets", "stylesheets", "overrides", "hooks"]   ← WRONG
```

The actual code default (unchanged since v0.6.0) is:

```text
["includes", "stylesheets", "overrides", "hooks"]              ← CORRECT
```

This is an "inverted ghost commit" — code that is correct, documented incorrectly. Any user
following the docs and assuming `docs/assets/` is excluded from all checks would be working from
a false premise. Worse: if they acted on that assumption and removed assets from the exclusion
list in their own config, they could inadvertently break Z104 detection across their entire docs
tree. Fixed: `configuration.mdx` (EN + IT) corrected, tip box added.

#### Rule R15 — Scope Integrity

Codified as a named invariant: **a resolved link is valid only if its target is within
`docs_root` or the adapter's declared static directories.** Filesystem existence outside this
perimeter is irrelevant. This was always implemented — D054 names and documents it.

#### `clean assets` Signature Alignment

The `clean assets` command now mirrors `check all` exactly: `PATH` argument (CEO-052 sovereign
root fix), `--engine`, `--exclude-dir`, `--include-dir`, `--quiet`, and full L1b adapter
metadata guardrail support.

---

### 🔬 Precision Calibration, CLI Symmetry & Governance (D055–D059, 2026-04-25)

A sprint focused on sensor accuracy, command-line symmetry, and engineering governance.

#### The Precision Calibration (D055)

Two subtle sensor calibration bugs surfaced and fixed.

**Z502 MDX Frontmatter Leak.** `_visible_word_count()` ran the frontmatter regex before stripping
MDX block-comments (`{/* … */}`). MDX files that open with an SPDX/copyright header before the `---`
block caused the regex (anchored to `\A`) to miss the frontmatter entirely — leaking key-value pairs
into the word count. A page with a `title`, `description`, and `sidebar_position` in frontmatter plus
10 prose words was incorrectly reported as "53 words" instead of "10 words", suppressing a legitimate
Z502 short-content finding. Fix: strip MDX/HTML comments first, then run frontmatter regex. Pure function.

**Z105 `pathname:///` False Positive.** The Docusaurus "Diplomatic Courier" pattern uses
`pathname:///assets/file.html` to link to static assets without a domain. `urlsplit` parses this as
`scheme="pathname"`, `path="/assets/file.html"`. The Z105 portability gate was firing on the leading
`/` of the URI path component — which is a URI convention artifact, not a server-root reference. Fix:
gate conditioned on `not parsed.scheme`. Any URL with a non-empty scheme is an engine protocol.
Rule R16 "Protocol Awareness" codified.

#### Universal Path Awareness (D056)

`zenzic score` and `zenzic diff` now accept an optional positional `PATH` argument — completing the
sovereign root fix (CEO-052) that `check all` received in D052. Running `zenzic score ../project-B`
from inside `project-A` now correctly loads `project-B`'s configuration and scores it. The banner
is printed before analysis begins. Rule R17 "CLI Symmetry" codified: all three analysis commands
accept the same optional PATH argument with identical semantics.

#### The Precedence Audit (D058)

A documentation audit found that the configuration priority hierarchy was incorrectly described in
three places: `README.md`, `README.it.md`, and the Configuration Reference. All three omitted CLI
flags from the priority chain. The correct 4-level hierarchy:

```text
CLI flags > zenzic.toml > [tool.zenzic] in pyproject.toml > built-in defaults
```

Fixed across all documentation surfaces (EN + IT).

#### The Law of Contemporary Testimony (D059)

A governance sprint codifying the principle that code and documentation are a single, indivisible
unit of work. All three Obsidian Ledgers updated with the Law of Contemporary Testimony as a
mandatory policy: no task can be marked complete if the documentation still reflects old behavior.
[CLOSING PROTOCOL] Step 0 "Pre-Task Alignment" and enhanced Step 3 "Contemporary Check" bullets
added to prevent documentation drift from accumulating silently.

---

### 🌐 Total CLI Symmetry (D060, 2026-04-25)

The final sprint before v0.7.0 ships: **every** filesystem-interacting CLI command in Zenzic now
accepts an optional `PATH` argument with full sovereign root semantics.

#### Universal PATH coverage

All six `check` sub-commands — `links`, `orphans`, `snippets`, `placeholders`, `assets`,
`references` — now mirror the path-awareness of `check all`. Run any individual check against
a remote project without changing directory:

```bash
zenzic check links   ../other-project       # links in a sibling repo
zenzic check orphans content/               # orphans in a sub-directory
zenzic check assets  /abs/path/to/docs      # assets check on an absolute path
```

Configuration follows the target, not the caller — a team running Zenzic in a CI pipeline
can now point at any branch checkout, any mounted volume, any workspace path.

#### The Nomad: `init` goes remote

`zenzic init <path>` bootstraps a remote directory. The directory is created if it does not
exist. Engine auto-detection runs on the target:

```bash
zenzic init ../new-project                  # scaffold zenzic.toml at target, not CWD
zenzic init /workspace/brand-new-docs       # absolute paths accepted; directory created
```

The caller's CWD is never modified. This is the "Nomad" mode — Zenzic follows you wherever
you work.

---

### 🗺 The Genesis Nomad Enforcement (D062, 2026-04-25)

After adding PATH awareness everywhere, D062 closes the loop on operator experience and
documentation.

#### Banner & Hint Sync

Every `check` sub-command now prints the resolved target path immediately after the Obsidian
header when a `PATH` argument is supplied:

```text
  Scanning: ../other-project/docs
```

`zenzic init <path>` shows:

```text
  Target: ../new-project
```

No more guessing which root Zenzic is scanning — the active sovereign root is visible before
the first result appears.

#### Sovereign Root Protocol — now documented

`docs/explanation/architecture.mdx` (English + Italian) gains a new **Sovereign Root Protocol**
section explaining the three-step sovereignty mechanism, the Genesis Nomad invariants, and the
Context Hijacking problem that motivated the design. New contributors and CI engineers now have
a canonical reference for why PATH arguments behave the way they do.

---

### 📖 The Maturity Narrative (D061, 2026-04-25)

The v0.7.0 launch blog article has been revised as a **case study in software engineering
maturity** — not a feature announcement. The revision (English + Italian simultaneously,
per the Law of Contemporary Testimony) adds four new sections:

**"Treating Documentation as Untrusted Input"** — the thesis: documentation is input, and
should be treated with the same skepticism security engineers apply to user data. The
discipline transfer from application security to documentation quality is what "Obsidian
Maturity" actually means.

**"The Precision Sprint"** — narrative of BUG-012 (Z502 MDX frontmatter leak) and BUG-013
(Z105 `pathname:///` false positive elimination). The section explains why false positives
are more damaging than false negatives: a scanner that cries wolf trains engineers to
suppress its output.

**"Total CLI Symmetry: The Sovereign Root Protocol"** — covers D060 and D062 with terminal
output examples showing the new `Scanning:` banner hint. The sovereign root contract in
plain language: configuration follows the target, not the caller.

**"The Law of Contemporary Testimony"** — codifies CEO-059 as an engineering principle.
Code and documentation are a single indivisible unit. Later compounds. The Law makes
"later" unconstitutional.

CTA updated: `uvx zenzic lab` replaces the old `pip install zenzic; zenzic check all`.

---

### 🧹 The Obsidian Hygiene (D063, 2026-04-25)

A forensic sweep of all production source in `src/zenzic/` for `TODO`, `FIXME`, and `HACK`
markers — the prerequisite for a "Stable" release designation. Every match found was
intentional production logic:

| File | Line | Nature |
|:-----|:----:|:-------|
| `core/codes.py:35` | Z501 code description mentioning "TODO content" | Rule definition |
| `cli/_standalone.py:617,623` | `if "TODO" in line:` | The Z501 detector itself |
| `cli/_check.py:663` | Docstring: "Detect pages with … TODOs/stubs" | Rule documentation |
| `models/config.py:317` | "TODO" in example error message string | Documentation string |

**Verdict:** Zero technical debt markers in production source. The v0.7.0 "Stable" codebase is
clean. No GitHub Issues opened, no code removed.

---

### 🔴 Operation Matrix Laboratory (D064, 2026-04-25)

The `zenzic lab` command graduates from a flat eleven-act showcase to a structured sixteen-act
matrix organised into four thematic sections. Six new example projects exercise the full
defence surface of the Sentinel — from Red/Blue team attack scenarios to rule-specific
stress tests.

#### New Example Projects

**`examples/os/unix-security/`** — the Blood Sentinel gauntlet. Three attack documents
(Red Team) — `deep-traversal.md` (multi-hop `../` chains), `obfuscated.md` (credentials
in tables, blockquotes, link titles, URL parameters), and `fenced.md` (credentials inside
`bash`, `yaml`, and `text` code fences, including a PEM key fragment). The Shield treats
no line as invisible. `check all` exits 2 — BREACH.

**`examples/os/win-integrity/`** — Windows portability guard. Two documents embedding
Windows-style filesystem paths (`/C:/`, `/D:/`, `/Z:/`, `/UNC/server/share/`, `file:///`)
as Markdown link targets. Each is environment-dependent and triggers Z105 (ABSOLUTE_LINK).
`check links` exits 1.

**`examples/rules/z100-link-graph/`** — adversarial link topology. A five-node graph with
circular broken anchors (Z102 ×13) and two links to non-existent files (Z104 ×2). Validates
the scanner's cycle-aware detection and FILE_NOT_FOUND path resolution under load.

**`examples/rules/z200-shield/`** — Shield extreme. Three obfuscation vectors:
Base64-encoded credentials, single- and double-pass percent-encoded patterns, and mixed-case
prefix randomisation (`AkIa`, `Sk-`, `GhP_`, `Sk_LiVe_`, `XoXb-`). The Shield normalises
content before pattern matching — all three techniques are detected. `check references` exits 2.

**`examples/rules/z400-seo/`** — SEO gap mass detection. Three subdirectories each missing
an `index.md` (Z401 ×3) and one `orphan.md` page with zero inbound links (Z402 ×1).
A realistic documentation structure with intentional coverage gaps. `check seo` exits 1.

**`examples/rules/z500-quality/`** — quality gate stress. Three stub documents (under-50-word
`stub-alpha.md`, `TODO`-marked `stub-beta.md`, `FIXME`-marked `stub-gamma.md`) triggering
Z501 PLACEHOLDER, plus `bad-snippet.md` with an `@include` to a nonexistent snippet
triggering Z503 SNIPPET_NOT_FOUND. `check quality` exits 1.

#### `zenzic lab` UI: Four Sections

```text
⬡  ZENZIC LAB  v0.7.0

  🛡  OS & Environment Guardrails         (Acts  0–3)
  🔗  Structural & SEO Integrity          (Acts  4–6)
  🏢  Enterprise Adapters & Migration     (Acts  7–10)
  🔴  Red/Blue Team Matrix                (Acts 11–16)
```

Each section renders as a separate `ROUNDED` Rich table with its thematic icon header.
Acts 11 and 14 are BREACH acts. Acts 12, 13, 15, and 16 are FAIL acts.

#### `examples/run_demo.sh`

Section banner comments added for all four thematic sections. Acts 9 and 10 (MkDocs and
Zensical favicon guards — present in `_lab.py` since D060 but absent from the demo script)
are now included. Acts 11–16 follow with correct expected exit codes (exit 2 for BREACH).

---

### 🎯 The Range Master Protocol (D069, 2026-04-25)

The `zenzic lab` command graduates from a fixed integer argument to a full range-aware
interface. A user who wants to stress-test the entire Red/Blue Team Matrix no longer needs
to issue six separate commands.

#### `parse_act_range()` — The Core Primitive

A new pure function `parse_act_range(raw: str) -> list[int]` encapsulates all parsing
logic with three accepted forms:

```text
"3"      → [3]           (single act)
"11-16"  → [11, 12, 13, 14, 15, 16]   (inclusive range)
"all"    → [0, 1, 2, …, 16]            (all 17 acts)
```

Invalid input (non-integer bounds, reversed range, out-of-range acts) produces an
`ObsidianUI.print_exception_alert()` panel — a styled, actionable error rather than a
raw Python traceback.

#### Sequence Header

When more than one act is selected, the Lab prints a `LAB SEQUENCE: Running Acts N
through M …` banner before execution, giving the operator a clear scope declaration.

#### `zenzic lab all` — The Full Tour

`zenzic lab all` runs all 17 acts in ascending order and produces the Full Run Summary
table. Acts 11 and 14 (BREACH expectations) and Acts 0, 2, 9, 10, 12, 13, 15, 16 (FAIL
expectations) are all verified in a single invocation.

#### Contemporary Testimony

`docs/reference/cli.mdx` (EN + IT) now includes a `## Interactive Lab` section
documenting act selection syntax, the four thematic sections, outcome labels, and usage
examples — fulfilling CEO-059.

---

### 🔍 The Ghost Content Fix (D072, 2026-04-25)

#### Root Cause

`_first_content_line()` used a single regex call anchored to `\A` via
`_FRONTMATTER_RE.match(text)`. Every file following REUSE best practice opens with one or
more `<!-- SPDX-FileCopyrightText: … -->` lines. Because `<` is not whitespace, the
anchored frontmatter regex failed to match — and the function fell back to `return 1`,
pointing the `❱` diagnostic arrow at the licence header rather than the first prose word.

The CEO named this **"The Blind Notary Paradox"**: a sentinel that could count correctly
but pointed at the bureaucracy instead of the poverty.

#### Fix

`_first_content_line()` is rewritten as a three-phase line-by-line walker:

| Phase | What it skips |
| :--- | :--- |
| 1 | Leading HTML (`<!-- … -->`) and MDX (`{/* … */}`) comments, including multi-line |
| 2 | YAML frontmatter (`--- … ---`) block, if present after comments |
| 3 | Blank lines between the above and the first prose word |

`_visible_word_count()` was unaffected — comment stripping before frontmatter detection
was already correct since D055. Only the pointer was broken.

#### The SPDX Trap Test

New regression test: a file with 5 SPDX HTML comment lines + 10-line YAML frontmatter +
the single word `FINE`. Asserts `line_no` resolves to the line containing `FINE`.

---

Zenzic is developed by **PythonWoods**, based in Italy, and committed to the craft of high-performance, deterministic Python engineering.

[**Read the Full Documentation →**](https://zenzic.dev)
