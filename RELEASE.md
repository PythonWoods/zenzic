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
