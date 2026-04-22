# Zenzic Agent Guidelines — v0.7.0 "Obsidian Maturity" Stable

Zenzic is the high-performance, engine-agnostic Safe Harbor for Markdown documentation.
It is a STABLE product. Agents must prioritize precision, security, and "Value-First" communication.

---

## 🎯 Mission: The Safe Harbor

- **Target:** Engineers, Technical Writers, and curious users.
- **Philosophy:** "If the engine builds the site, Zenzic guarantees the source."
- **Communication:** README is a Landing Page, not a manual. Move technical deep-dives to the documentation portal (zenzic.dev).

---

## 🚀 Key Features (v0.7.0 — Obsidian Maturity Stable)

- **Instant Entry:** `uvx zenzic check all ./path` is the primary curiosity path.
- **Zenzic Lab:** 10 interactive Acts for onboarding (zero-config showroom). Run `zenzic lab` to see the menu; `zenzic lab <N>` to run a specific act.
- **Standalone Mode:** Default engine for pure Markdown projects with no recognised build system. Replaces the old "Vanilla" identity entirely.
- **Zensical Bridge:** Transparent Proxy for `mkdocs.yml` compatibility under `engine = "zensical"`.
- **Enterprise Docusaurus:** Full versioning, `@site/` alias, and slug logic alignment.
- **Offline Mode:** `--offline` flag for flat `.html` URL structure.
- **SEO Guardrail:** `Z401 MISSING_DIRECTORY_INDEX` detection for directories without a landing page.
- **Finding Codes (Zxxx):** Every diagnostic carries a unique `Zxxx` identifier for enterprise-grade auditing and future filtering.

---

## 🧱 The 3 Pillars (Non-Negotiable)

1. **Lint the Source:** Never depend on HTML output. Analyze raw Markdown and configs.
2. **No Subprocesses:** 100% pure Python. No `subprocess.run`, no Node.js execution.
3. **Pure Functions First:** Deterministic logic. No I/O in hot-path loops.

---

## 🛡️ Core Laws for Code

- **Zero I/O in hot paths:** No `Path.exists()` or `open()` inside link/file loops.
- **Mandatory ExclusionManager:** No discovery without an explicit exclusion manager.
- **Exit Codes:** 0 (Success), 1 (Quality), 2 (Shield/Secrets), 3 (Blood Sentinel/Fatal).
- **Finding Codes:** Every `Finding` object must carry a `Zxxx` code from `src/zenzic/core/codes.py`. Never hardcode a raw string code; always use `codes.normalize()`.

---

## 📐 Architecture Map

```text
src/zenzic/
  cli.py                   — Typer CLI entry-points; builds Finding objects via _to_findings()
  lab.py                   — Interactive showcase (9 Acts); menu-driven with positional arg
  core/
    adapter.py             — Public re-exports (StandaloneAdapter, MkDocsAdapter, …)
    adapters/
      _standalone.py       — StandaloneAdapter: no-op engine for pure Markdown projects
      _mkdocs.py           — MkDocs engine adapter
      _docusaurus.py       — Docusaurus v3 engine adapter
      _zensical.py         — Zensical engine adapter (+ Transparent Proxy)
      _factory.py          — get_adapter() factory; contains vanilla→standalone migration guard
      __init__.py          — Public adapter registry
    codes.py               — Zxxx finding code registry (SINGLE SOURCE OF TRUTH)
    reporter.py            — SentinelReporter; renders Finding objects to Rich output
    scanner.py             — File discovery, orphan detection, shield bridge
    validator.py           — Link / anchor / path-traversal validation
    rules.py               — VSM-based rule engine (Z001, Z002)
    shield.py              — Credential scanner (exits 2/3)
    scorer.py              — Quality score engine
  models/
    config.py              — ZenzicConfig / BuildContext (Pydantic)
    vsm.py                 — Virtual Site Map (Route, build_vsm, detect_collisions)
    references.py          — Reference integrity (IntegrityReport, ReferenceFinding)
  ui.py                    — Shared Rich colour constants and emoji helpers
tests/
  test_standalone_mode.py  — StandaloneAdapter unit tests + factory routing
  test_vsm.py              — Virtual Site Map tests
  test_blue_vsm_edge.py    — VSM edge-case stress tests
  test_protocol_evolution.py — Adapter protocol compliance + Hypothesis stress tests
  test_cli.py              — CLI integration tests (Typer runner)
  test_scanner.py          — Scanner / orphan / i18n tests
  test_rules.py            — Rule engine tests
  test_shield.py           — Shield / credential detection tests
```

---

## 🔎 Finding Code Standard (Zxxx)

All diagnostics emitted by Zenzic carry a `Zxxx` code. The registry is in
`src/zenzic/core/codes.py`. **Never add a new finding without registering its code there first.**

| Range | Category | Examples |
|-------|----------|---------|
| Z1xx | Link Integrity | Z101 LINK_BROKEN, Z102 ANCHOR_MISSING, Z104 FILE_NOT_FOUND |
| Z2xx | Security | Z201 SHIELD_SECRET, Z202 PATH_TRAVERSAL |
| Z3xx | Reference Integrity | Z301 DANGLING_REF, Z302 DEAD_DEF |
| Z4xx | Structure | Z401 MISSING_DIRECTORY_INDEX, Z402 ORPHAN_PAGE |
| Z5xx | Content Quality | Z501 PLACEHOLDER, Z503 SNIPPET_ERROR |
| Z9xx | Engine / System | Z902 RULE_TIMEOUT |

When creating a `Finding`, always call `codes.normalize(raw_code)` to map legacy strings to canonical `Zxxx` codes. The `_to_findings()` function in `cli.py` is the authorised conversion point.

---

## 🏭 Adapter Identity Rules

- **"standalone"** is the canonical engine name for projects with no build config. Use `StandaloneAdapter`.
- **"vanilla"** is a removed legacy name. Any usage raises `ConfigurationError` with code `Z000`.
- `pyproject.toml` entry-point: `standalone = "zenzic.core.adapters:StandaloneAdapter"`.
- In Standalone Mode, navigation-based checks (orphan detection) are disabled because there is no declared nav.
- When `zenzic init` finds no engine config, it writes `engine = "standalone"` in the `[build_context]` block.

---

## 🧪 Quality Gate

- **Coverage:** ≥ 80% mandatory.
- **Mutation:** Mutmut audit on `rules.py` and `shield.py`.
- **Property Testing:** Hypothesis for `resolver.py` and adapter stress-testing.
- **Test naming:** All test functions relating to the Standalone adapter use the prefix `test_standalone_*`.

---

## 📝 README Restyling Rules

When editing `README.md` or `README.it.md`:

1. **Above the Fold:** Hook + uvx command + Quick Start + Sentinel Report must be visible within 2 scrolls.
2. **Problem/Solution:** Use tables to contrast "Without Zenzic" vs "With Zenzic".
3. **Deduplicate:** Technical implementation details belong in `/docs/internals` on zenzic.dev.
4. **Bilingual Parity:** EN and IT must be perfectly mirrored in structure and quality.
5. **Branding:** Keep "Shield", "Blood Sentinel", "VSM", "Ghost Routes" as-is (Proper Nouns).
6. **Standalone, not Vanilla:** Never write "Vanilla Mode" in user-facing copy. Use "Standalone Mode".
7. **Footer Social Links:** GitHub + Journal are the only authorised social links. Never add X.com / Twitter. Footer identity line must always include `in Italy 🇮🇹` (EN) / `in Italia 🇮🇹` (IT).
8. **No title heading:** README opens with the wordmark SVG, no `# 🛡️ Zenzic` heading. No Roadmap section.
9. **Chronicles position:** The Obsidian Chronicles section always precedes the footer.

---

## 🧹 Maintenance & Sunset Clauses (Technical Debt Tracking)

### 1. Vanilla-to-Standalone Migration Guard

- **Status:** ✅ REMOVED in v0.7.0.
- **Location (historical):** `src/zenzic/core/adapters/_factory.py`.
- **Behavior (historical):** Raised `ConfigurationError [Z000]` for `engine = "vanilla"` users.
- **Sunset Target:** **v0.7.0** — completed. Guard deleted. Zero-legacy codebase achieved.

### 2. Finding Codes (Zxxx)

- **Standard:** All diagnostics must use the `Zxxx` format.
- **Rule:** Never introduce a new finding string without a corresponding code in `src/zenzic/core/codes.py`.

---

## 🗺️ Sprint History (for institutional memory)

### Direttiva 036 — Finding Code Mapping

Codified all diagnostic outputs into the `Zxxx` scheme. `codes.py` created as single source of truth.

### Direttiva 037 — Standalone Renaissance

Full rename: `VanillaAdapter` → `StandaloneAdapter`, `_vanilla.py` → `_standalone.py`, entry-point `vanilla` → `standalone`. Breaking change: `engine = "vanilla"` raises `ConfigurationError [Z000]`. Test suite fully migrated to `test_standalone_mode.py`.

### Direttiva 038 — Final Audit Record

CHANGELOG.md, CHANGELOG.it.md, and RELEASE.md updated to reflect the Breaking Change (Vanilla → Standalone), the Zxxx code introduction, and the interactive Lab menu.

### Direttiva 039 — The Guardrail Lifecycle

Migration guard in `_factory.py` annotated with `# TODO: Remove this migration guard in v0.7.0.` and error message prefixed with `[Z000]`. Docstring clarified.

### Direttiva 040 — Institutional Memory

This file (`.github/copilot-instructions.md`) created / restored as the canonical agent briefing document, embedding all sprint directives and sunset clauses for permanent institutional memory.

### Direttiva 076/077/078/079 — Sprint v0.6.2 "Obsidian Integrity"

**Version:** 0.7.0 · **Date:** 2026-04-22

#### Direttiva 077 — Z104 Suggestion Engine

`difflib.get_close_matches` (cutoff 0.6) integrated into `validator.py` at the `FILE_NOT_FOUND` case.
The `_known_rel_paths` list is pre-computed from `md_contents` before Pass 2 begins — no disk I/O in hot path.
Error message appends `💡 Did you mean: '...'?` when a close match is found.

#### Direttiva 078 — Vanilla Purge

All user-facing copy purged of "Vanilla mode" and "VanillaAdapter". Replaced with "Standalone Mode" and "StandaloneAdapter".
Affected: `README.md`, `README.it.md`, `examples/vanilla/`, `examples/standalone-markdown/`, `examples/custom-dir-target/`, `examples/single-file-target/`.
Engineering Ledger (HTML table, three non-negotiable contracts) replaced the "Design Philosophy" prose section in both READMEs.
Standalone Mode now explicitly declares: orphan detection (`Z402`) is disabled without a navigation contract.

#### Direttiva 079 — Sentinel Mesh Tightening

**Forensic finding:** `excluded_external_urls` contained `"https://zenzic.dev/"` — a blanket bypass
added when the site was undeployed. After the Diátaxis restructure, three links in `README.md` had
already rotted silently behind this curtain:

- `/docs/usage/badges/` (old) → `/docs/how-to/add-badges/` (correct)
- `/docs/guides/ci-cd/` (old) → `/docs/how-to/configure-ci-cd/` (correct)
- `/docs/internals/architecture-overview/` (old) → `/docs/explanation/architecture/` (correct)

**Fix:** Blanket exclusion removed. Links corrected in `README.md` and `README.it.md`.
`zenzic.toml` now carries a `⚠ PERIMETER INVARIANT` comment documenting that `docs_dir = "."`
is a safety invariant (README.md must always be inside the perimeter).
`zenzic check all` on the core repo now exits 0 with the corrected links.

### Direttiva 082/083/084/085/086 — The Obsidian Mirror Pass

**Version:** 0.7.0 · **Date:** 2026-04-22

Z404 CONFIG_ASSET_MISSING introduced for Docusaurus (`check_config_assets()` in `_docusaurus.py`).
Lab Obsidian Seal added. GitHub release workflow for zenzic-doc. Favicon/OG meta tag fixes.
`finding-codes.mdx` Docusaurus Z404 section added. zenzic-doc v0.6.1 deprecated.

### Direttiva CEO 087 — The Agnostic Universalism

**Version:** 0.7.0 · **Date:** 2026-04-22

**Core fix:** Z404 was Docusaurus-only — architectural flaw for a Safe Harbor claiming engine-agnosticism.

#### Changes

- `_mkdocs.py`: `check_config_assets(repo_root)` added — checks `theme.favicon` + `theme.logo` (image-ext filter, relative to `docs_dir/`).
- `_zensical.py`: `check_config_assets(repo_root)` added — checks `[project].favicon` + `[project].logo` (same filter, relative to `[project].docs_dir/`).
- `cli.py`: docusaurus-only `if engine == "docusaurus"` block replaced with multi-engine dispatch covering all three engines.
- `finding-codes.mdx` (EN + IT): Z404 section rewritten as agnostic — per-engine field tables, per-engine remediation snippets, adapter coverage updated.
- `examples/mkdocs-z404/` + `examples/zensical-z404/`: New Lab fixtures for Z404 demo.
- `lab.py`: Acts 9 (MkDocs Favicon Guard) and 10 (Zensical Logo Guard) added. Validator updated to `0–10`.

### Direttive 109–116 — Typography, Navigation & Layout Polish

**Version:** 0.7.0 · **Date:** 2026-04-22

Visual polish sprint for zenzic-doc: typography system (Geist + JetBrains Mono), navigation arrows, responsive layout hardening, hero/feature section refinements. Committed to `release/v0.7.0`.

### Direttiva 117 — `pathname:` Protocol Support

**Version:** 0.7.0 · **Date:** 2026-04-22

`validator.py` now recognises the Docusaurus `pathname:///` escape hatch and skips those links without emitting a false-positive Z101. Tests added. `reference/engines.mdx` (EN + IT) documents the behaviour and scope.

### Direttive 118–119 — Blog Title Consistency & Sibling Release Protocol

**Version:** 0.7.0 · **Date:** 2026-04-22

- **D118:** blog list `h2 a` colors locked across `:visited`/`:active`/`:hover` — Zinc-700 light, White/Silk dark, Cyan on hover only.
- **D119:** RELEASE.md in core repo rewritten as Sibling Release Protocol. `scripts/bump-version.sh` + `just bump` recipe added to `zenzic-doc`. Badge corrected v0.6.2 → v0.7.0.

### Direttiva 122 — Governance Pack

**Version:** 0.7.0 · **Date:** 2026-04-22

Created `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff`, `SECURITY.md` in `zenzic-doc`. `REUSE.toml` updated to full compliance.

### Direttive 123–125 — Global Brand Sync

**Version:** 0.7.0 · **Date:** 2026-04-22

- Both `README.md` and `README.it.md`: `# 🛡️ Zenzic` title removed (wordmark-only), Roadmap removed, Obsidian Chronicles added, PythonWoods Obsidian Signature footer added.
- `assets/brand/pythonwoods-logo.svg` added to core repo with REUSE sidecar. REUSE 256/256.
- `zenzic-doc/README.md`: 4 badges added (Docs CI, License, REUSE, Diátaxis), Node 20→22 corrected, Chronicles added, footer aligned.

### Direttiva CEO 127 — The Sovereign Identity Protocol

**Version:** 0.7.0 · **Date:** 2026-04-22

**Brand audit and correction:** X.com links removed from all user-facing files. Italian identity restored.

- `README.md`: X (Twitter) link removed. Footer now reads `Engineered with precision by PythonWoods in Italy 🇮🇹`.
- `README.it.md`: X (Twitter) link removed. Footer now reads `Ingegnerizzato con precisione da PythonWoods in Italia 🇮🇹`.
- `zenzic-doc/README.md`: X (Twitter) link removed. Italian flag 🇮🇹 restored.
- `RELEASE.md` (both repos): `🇮🇹` flag already present — confirmed clean.
- `blog/authors.yml`: already X.com-free — confirmed clean.
- **Rule added to README Restyling Rules:** Never add X.com / Twitter links. GitHub + Journal are the only authorised social links.
- `RELEASE.md` signatures aligned: cross-reference added between core ↔ doc RELEASE files.
- `pyproject.toml` bumpversion: `RELEASE.md` added as a file target.
- `bump-version.sh` (zenzic-doc): RELEASE.md pattern generalised to `v{old}` covering all occurrences.
