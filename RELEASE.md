<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# 🛡️ Zenzic v0.7.0 — Quartz Maturity

## "Engine-Agnostic. Integrity-Complete. The True Safe Harbor."

**Zenzic v0.7.0** marks the consolidation of our core architecture into a definitive,
engine-agnostic documentation integrity shield. This is not an incremental update —
it is a new standard of precision.

**v0.6.x is superseded.** v0.7.0 is the canonical reference for all deployments.

---

## ⚠️ Breaking Changes

| Change | Migration |
| :--- | :--- |
| MkDocs plugin (`zenzic.integrations.mkdocs`) removed | Remove `plugins: - zenzic` from `mkdocs.yml`; add `zenzic check all` as a CI step |
| `engine = "vanilla"` removed | Replace with `engine = "standalone"` in `zenzic.toml` |
| `zenzic plugins` command removed | Use `zenzic inspect capabilities` |

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

## 🛡️ Security

**Sealed 5 critical bypass vectors — including the S2 Red Team attack vector (Base64) — during AI-driven red-team audit.**

The Red/Blue Team Matrix (Acts 11–16) revealed and verified defences against:
deep `../` path traversal chains targeting OS system directories (Blood Sentinel — exit 3),
credential obfuscation via Base64 encoding, percent-encoding, and mixed-case normalization
(Shield — exit 2), Windows absolute path injection (`C:\`, UNC shares), and cross-line
credential splitting via the ZRT-007 lookback buffer.

**Base64 Speculative Decoder (v0.7.0 D095):** The Shield now decodes candidate Base64 tokens
and re-scans the decoded text. A GitHub PAT encoded as `Z2hwXzEyMzQ...` in frontmatter
triggers Z201 and exits 2. Attack vector S2 sealed.

**KL-002 portability fix:** `os.path.normcase` applied to the Blood Sentinel boundary check
so that mixed-case paths on APFS/NTFS no longer produce false-positive traversal findings.

Full audit report: [Quartz Tribunal Audit](https://zenzic.dev/docs/explanation/audit-v070-quartz-siege)

**Multi-Root Shield:** Cross-locale relative links no longer trigger false-positive
`PATH_TRAVERSAL_SUSPICIOUS` while preserving detection of links that escape every
authorised root.

---

## 📋 What's New at a Glance

- **Law of Contemporary Testimony** — code and documentation updated in the same commit;
  documentation that contradicts the code is classified as a bug.
- **`zenzic score [PATH]` and `zenzic diff [PATH]`** — full PATH sovereignty for scoring.
- **`--no-color` / `--force-color`** and `NO_COLOR`/`FORCE_COLOR` environment variables.
- **`--offline` mode** — flat URL resolution for USB/intranet deployments.
- **`--quiet` flag** — single-line summary for pre-commit and CI silent builders.
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
