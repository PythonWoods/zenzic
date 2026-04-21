# Zenzic Agent Guidelines — v0.6.1 "Obsidian Glass" Stable

Zenzic is the high-performance, engine-agnostic Safe Harbor for Markdown documentation.
It is a STABLE product. Agents must prioritize precision, security, and "Value-First" communication.

---

## 🎯 Mission: The Safe Harbor

- **Target:** Engineers, Technical Writers, and curious users.
- **Philosophy:** "If the engine builds the site, Zenzic guarantees the source."
- **Communication:** README is a Landing Page, not a manual. Move technical deep-dives to the documentation portal (zenzic.dev).

---

## 🚀 Key Features (v0.6.1 — Obsidian Glass Stable)

- **Instant Entry:** `uvx zenzic check all ./path` is the primary curiosity path.
- **Zenzic Lab:** 9 interactive Acts for onboarding (zero-config showroom). Run `zenzic lab` to see the menu; `zenzic lab <N>` to run a specific act.
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

---

## 🧹 Maintenance & Sunset Clauses (Technical Debt Tracking)

### 1. Vanilla-to-Standalone Migration Guard

- **Status:** Deprecated.
- **Location:** `src/zenzic/core/adapters/_factory.py` (check for `engine == "vanilla"`).
- **Behavior:** Raises a `ConfigurationError` with code `Z000` to guide users to `engine = "standalone"`.
- **Sunset Target:** **v0.7.0**.
- **Instruction:** Do NOT remove this guard in 0.6.x patches. MUST be deleted entirely in the 0.7.0 release to achieve zero-legacy codebase.

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
