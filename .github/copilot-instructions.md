# 🛡️ ZENZIC CORE — Obsidian Ledger v0.7.0 "Obsidian Maturity"

> **Single Source of Truth for all agents and contributors.**
> Schema: [MANIFESTO] → [POLICIES] → [ARCHITECTURE] → [ADR] → [CHRONICLES] → [SPRINT LOG]

---

## [MANIFESTO] — The Safe Harbor Vision

Zenzic is not a build tool. It is a **Static Analysis Framework** that treats documentation as **Untrusted Input**. Its mission is to provide a "Safe Harbor" (Porto Sicuro): a guarantee that the source is structurally sound, link-complete, and secret-free — regardless of which build engine consumes it.

**Tagline:** *"If the engine builds the site, Zenzic guarantees the source."*

**Target users:** Engineers, Technical Writers, DevOps teams running CI gates.

### The 3 Pillars (Non-Negotiable)

1. **[INVARIANT] Lint the Source, Not the Build.** Analyze raw Markdown and configs. Never depend on HTML output. Catch errors *before* the build starts.
2. **[INVARIANT] Zero Subprocesses.** 100% pure Python. No `subprocess`, no `os.system`, no Node.js execution. Total portability and Zero-Trust execution.
3. **[INVARIANT] Pure Functions First.** Analysis logic is deterministic. I/O is isolated at the edges (Discovery and Reporting). No I/O in hot-path loops.

### How Zenzic "Thinks": The VSM

Zenzic builds a **Virtual Site Map (VSM)** — a projection of the final site in memory. This allows validating "Ghost Routes" (i18n fallbacks, versioned slugs) that do not exist physically on disk. No build required.

---

## [CLOSING PROTOCOL] — Mandatory Sprint Closure Checklist

> **[MANDATORY]** A sprint is not closed until every step below is complete.
> Skipping any step is a **Class 1 violation (Technical Debt)** — the successor agent inherits a ghost, not a project.

### Step 1 — Update This File

- [ ] New architectural facts? → Update **[ARCHITECTURE]**
- [ ] New decisions made? → Add an **[ADR]** entry (tagged `[DECISION]`)
- [ ] Bug found and fixed? → Add a **[CHRONICLES]** entry (tagged `[BUG-xxx]` / `[LESSON]`)
- [ ] Sprint complete? → Add entry to **[SPRINT LOG]**

### Step 2 — Update Changelogs

- [ ] `CHANGELOG.md` — add sprint section under current version heading
- [ ] `CHANGELOG.it.md` — Italian translation of the same section
- [ ] `RELEASE.md` — marketing prose section for the sprint

### Step 3 — Staleness Audit

- [ ] `README.md` / `README.it.md` — check: version numbers, feature lists, CLI flag examples, Z-code table, architecture descriptions
- [ ] No `.mdx` audit required here — `zenzic-doc` is responsible for its own documentation

### Step 4 — Verification Gate

- [ ] Full test suite: `nox -s tests`
- [ ] Self-audit: `zenzic check all` on this repo (exit 0 required)
- [ ] Stage and review the full diff before committing

---

## [POLICIES] — Immutable Operational Laws

### Core Laws

- **[RULE R01] Zero I/O in hot paths.** No `Path.exists()` or `open()` inside link/file loops.
- **[RULE R02] Mandatory ExclusionManager.** No file discovery without an explicit `LayeredExclusionManager`.
- **[RULE R03] Finding Codes are mandatory.** Every `Finding` object must carry a `Zxxx` code from `src/zenzic/core/codes.py`. Never hardcode a raw string; always call `codes.normalize()`. The `_to_findings()` function in `cli/_check.py` is the authorised conversion point.
- **[RULE R04] Exit code contract is inviolable.** 0 = Success, 1 = Quality, 2 = Shield/Secrets, 3 = Blood Sentinel/Fatal. Exit codes 2 and 3 are **never suppressible** by `--exit-zero`.
- **[RULE R05] Core never imports upward.** Modules in `src/zenzic/core/` must never import from `src/zenzic/cli/` or `src/zenzic/main.py`. Dependency direction: `cli → core → models`.
- **[RULE R06] Standalone, not Vanilla.** The engine name `"standalone"` is canonical for pure Markdown projects. `"vanilla"` raises `ConfigurationError [Z000]` — this guard is **permanent**.
- **[RULE R07] README is a landing page.** Move technical deep-dives to zenzic.dev. Never add Roadmap sections or X.com / Twitter links. Footer must always include `in Italy 🇮🇹` (EN) / `in Italia 🇮🇹` (IT). GitHub + Journal are the only authorised social links.
- **[RULE R08] No Subprocesses.** No `subprocess.run`, `os.system`, or any external process. Zenzic is 100% pure Python.
- **[RULE R09] Shield has priority.** The Shield must scan raw file content (every line including YAML frontmatter) before any other pass. See ZRT-001.
- **[RULE R10] SARIF output must be pure.** When `--format sarif` or `--format json`, no banner or non-JSON output may be written to stdout.
- **[RULE R11] Sovereign Sandbox (CEO-043).** [DECISION] The explicit `PATH` argument provided by the user is the sovereign sandbox root. Blood Sentinel guards escapes FROM the target, not the location OF the target. If `docs_root` falls outside `repo_root`, `repo_root` is dynamically reassigned to `docs_root`.
- **[RULE R12] Symmetry Guardrail (CEO-045).** [DECISION] Every structural change to the documentation hierarchy must be applied symmetrically across all supported locales. Missing translations are potential structural failures. Goal: Zero 404s on the language switcher.
- **[RULE R13] Intelligent Perimeter (CEO-050).** [DECISION] Metadata files consumed by adapters (e.g. `docusaurus.config.ts`, `mkdocs.yml`, `zensical.toml`) and universal infrastructure files (e.g. `package.json`, `pyproject.toml`) are **Level 1 System Guardrails** — permanently shielded from Z903 and all quality checks. Declare them in `BaseAdapter.get_metadata_files()` (L1b) and `SYSTEM_EXCLUDED_FILE_NAMES`/`SYSTEM_EXCLUDED_FILE_PATTERNS` (L1a). **Never ask the user to exclude them manually.**

### Exit Codes

| Code | Meaning | Suppressible by `--exit-zero`? |
|------|---------|-------------------------------|
| 0 | All checks passed | — |
| 1 | Quality findings (broken links, orphans, placeholders, etc.) | ✅ Yes |
| 2 | Shield security breach — credential detected (Z201) | ❌ Never |
| 3 | Blood Sentinel — system path traversal / fatal (Z202/Z203) | ❌ Never |

### Finding Code Standard (Zxxx)

Registry: `src/zenzic/core/codes.py` — **single source of truth**. Never add a finding without registering its code there first.

| Range | Category | Known Codes |
|-------|----------|-------------|
| Z1xx | Link Integrity | Z101 LINK_BROKEN, Z102 ANCHOR_MISSING, Z103 UNREACHABLE_LINK, Z104 FILE_NOT_FOUND, Z105 ABSOLUTE_PATH, Z106 ALT_TEXT_MISSING |
| Z2xx | Security | Z201 SHIELD_SECRET, Z202 PATH_TRAVERSAL, Z203 PATH_TRAVERSAL_SUSPICIOUS |
| Z3xx | Reference Integrity | Z301 DANGLING_REF, Z302 DEAD_DEF, Z303 CIRCULAR_LINK |
| Z4xx | Structure | Z401 MISSING_DIRECTORY_INDEX, Z402 ORPHAN_PAGE, Z403 SNIPPET_UNREACHABLE, Z404 CONFIG_ASSET_MISSING |
| Z5xx | Content Quality | Z501 PLACEHOLDER, Z502 SHORT_CONTENT, Z503 SNIPPET_ERROR, Z504 QUALITY_REGRESSION |
| Z9xx | Engine / System | Z901 RULE_ERROR, Z902 RULE_TIMEOUT, Z903 CONFIG_ERROR, Z904 DISCOVERY_ERROR |

### Adapter Identity Rules

- `"standalone"` — canonical name for projects with no build config. Uses `StandaloneAdapter`. In Standalone Mode, orphan detection (Z402) is disabled (no navigation contract).
- `"vanilla"` — **permanently removed** in v0.6.1. Any usage raises `ConfigurationError [Z000]`.
- `pyproject.toml` entry-point: `standalone = "zenzic.core.adapters:StandaloneAdapter"`.
- When `zenzic init` finds no engine config, it writes `engine = "standalone"`.

### Quality Gate

- **Coverage:** ≥ 80% mandatory.
- **Mutation score:** Target 75%+ on `rules.py`, `shield.py`, `reporter.py` (achieved 86.7% in v0.7.0 sprint).
- **Property Testing:** Hypothesis profiles — dev (50 examples), ci (500), purity (1000).
- **Cross-platform CI:** 3×3 matrix — OS: `[ubuntu, windows, macos]` × Python: `[3.11, 3.12, 3.13]`.

### README Restyling Rules

1. **Above the Fold:** Hook + `uvx` command + Quick Start + Sentinel Report visible within 2 scrolls.
2. **Problem/Solution:** Tables contrasting "Without Zenzic" vs "With Zenzic".
3. **Deduplicate:** Technical details belong at zenzic.dev.
4. **Bilingual Parity:** EN and IT must be perfectly mirrored in structure and quality.
5. **Branding:** Keep "Shield", "Blood Sentinel", "VSM", "Ghost Routes" as-is (Proper Nouns).
6. **Footer:** Must include `in Italy 🇮🇹` (EN) / `in Italia 🇮🇹` (IT). No X.com / Twitter.
7. **No title heading:** Opens with the wordmark SVG. No Roadmap section.
8. **Chronicles position:** Obsidian Chronicles section always precedes the footer.

### Memory Law — The Custodian's Contract

- **[INVARIANT] The [CLOSING PROTOCOL] is a non-negotiable Engineering Contract.**
  An agent that ends a session without completing it commits a Class 1 violation (Technical Debt). The successor inherits a ghost, not a project.
- **[INVARIANT] This file is the agent's only persistent memory.** Update it before the final commit — not after.
- **[INVARIANT] Definition of Done:** A sprint is not closed until [SPRINT LOG] is updated, CHANGELOG is current, and the staleness audit is complete.
- **[INVARIANT] Proactivity:** Agents must notify the Tech Lead when a code change contradicts or expands current guidelines.
- **[INVARIANT] Sovereignty:** This file is the single source of truth for agent behavior.

---

## [ARCHITECTURE] — Module Map (v0.7.0 Accurate)

```text
src/zenzic/
  main.py                   — Typer app factory; registers all CLI groups (check, inspect, clean, lab, …)
  rules.py                  — 6-line SDK façade; re-exports from core/rules.py (D064)
  cli/
    __init__.py             — Public CLI re-exports
    _check.py               — check sub-app: links, orphans, snippets, references, assets, all
    _inspect.py             — inspect sub-app: capabilities
    _clean.py               — clean sub-app
    _lab.py                 — lab command: 11 Acts (0–10), interactive showcase
    _standalone.py          — standalone commands: diff, init, score
    _shared.py              — shared helpers: _build_exclusion_manager, _validate_docs_root, _ui, console
  core/
    adapter.py              — Public re-exports: StandaloneAdapter, MkDocsAdapter, DocusaurusAdapter, …
    adapters/
      _base.py              — Abstract adapter protocol (AdapterProtocol)
      _standalone.py        — StandaloneAdapter: no-op for pure Markdown projects
      _mkdocs.py            — MkDocs engine adapter + check_config_assets()
      _docusaurus.py        — Docusaurus v3 adapter + check_config_assets()
      _zensical.py          — Zensical adapter + Transparent Proxy + check_config_assets()
      _factory.py           — get_adapter() factory; Z000 guard PERMANENT (vanilla removed)
      _utils.py             — Frontmatter extraction, build_metadata_cache, case_sensitive_exists
      __init__.py           — Adapter registry
    codes.py                — Zxxx finding code registry (SINGLE SOURCE OF TRUTH)
    reporter.py             — SentinelReporter; renders Finding objects to Rich output
    scanner.py              — File discovery, _visible_word_count, check_placeholder_content
    validator.py            — Link/anchor/path-traversal validation; Z104 Did-you-mean hints
    rules.py                — AdaptiveRuleEngine (auto parallel/sequential at 50-file threshold)
    shield.py               — Credential scanner; scan_lines_with_lookback; safe_read_line
    scorer.py               — Quality score engine
    discovery.py            — Universal discovery: walk_files, iter_markdown_sources
    exclusion.py            — LayeredExclusionManager (4-level hierarchy)
    resolver.py             — InMemoryPathResolver (multi-root, cross-locale links)
    cache.py                — Content-addressable CacheManager
    exceptions.py           — ConfigurationError, PluginContractError, ShieldViolation
    logging.py              — Rich logging handler
    ui.py                   — ObsidianPalette, ObsidianUI, make_banner (moved here in D062-B)
  models/
    config.py               — ZenzicConfig / BuildContext (Pydantic); 3-level config priority
    vsm.py                  — Virtual Site Map: Route, build_vsm, detect_collisions
    references.py           — Reference integrity: IntegrityReport, ReferenceFinding

tests/
  test_cli.py               — CLI integration tests (Typer runner)
  test_scanner.py           — Scanner / orphan / i18n tests
  test_validator.py         — Link/anchor/traversal validation tests
  test_rules.py             — Rule engine + mutant-kill tests
  test_shield.py            — Shield / credential detection
  test_redteam_remediation.py — Frontmatter Shield, ReDoS canary, normalizer
  test_shield_obfuscation.py — Bypass attempts: Unicode, HTML entities, lookback
  test_docusaurus_adapter.py — 65 tests for Docusaurus config parsing
  test_standalone_mode.py   — StandaloneAdapter unit tests + factory routing
  test_vsm.py + test_blue_vsm_edge.py — Virtual Site Map tests
  test_resolver.py          — InMemoryPathResolver tests
  test_cache.py             — CacheManager tests
  test_reporter.py          — SentinelReporter tests
  test_cli_e2e.py           — 8 end-to-end CLI security tests
  test_protocol_evolution.py — Adapter protocol compliance + Hypothesis stress tests
  guardians/
    test_i18n_path_integrity.py — i18n path traversal + locale root tests
```

**Config priority (3 levels):** `zenzic.toml` > `[tool.zenzic]` in `pyproject.toml` > built-in defaults.

---

## [ADR] — Architectural Decision Records

### ADR-001: Zxxx Finding Code Scheme (D036)

**[DECISION]** All diagnostics emitted by Zenzic carry a machine-readable `Zxxx` identifier.

- **Why:** Enterprise CI needs stable, filterable codes. Raw string messages are fragile across versions.
- **Result:** `codes.py` as single source of truth; `codes.normalize()` maps legacy strings to canonical codes.

### ADR-002: Standalone Renaissance — Removal of "Vanilla" (D037)

**[DECISION]** `VanillaAdapter` renamed to `StandaloneAdapter`; engine name `"vanilla"` raises `ConfigurationError [Z000]` permanently.

- **Why:** "Vanilla" was semantically ambiguous. "Standalone" correctly conveys "self-contained, no build system".
- **Invariant:** The Z000 guard in `_factory.py` is **permanent**. The `# TODO: Remove in v0.7.0` comment was deleted, but the guard remains indefinitely.

### ADR-003: Sovereign CLI — Removal of MkDocs Integration Plugin (D055/D066)

**[DECISION]** `zenzic.integrations.mkdocs` plugin and `src/zenzic/integrations/` directory deleted entirely in v0.7.0.

- **Why:** Zenzic is a Sovereign CLI, engine-agnostic. Embedding engine hooks contradicts Pillar 1 ("Lint the Source, Not the Build").
- **Migration:** `plugins: - zenzic` in `mkdocs.yml` → `zenzic check all --strict` as a CI step.
- **Also removed:** `zenzic plugins` command replaced by `zenzic inspect capabilities` (D068).

### ADR-004: Decentralized CLI Package (D062-B, D063, D064)

**[DECISION]** CLI layer split into a package `src/zenzic/cli/` with `src/zenzic/main.py` as Typer entry point.

- **D062-B:** `src/zenzic/ui.py` → `src/zenzic/core/ui.py` (Core Law: core never imports upward).
- **D063:** `src/zenzic/lab.py` → `src/zenzic/cli/_lab.py` (Lab is CLI orchestration, not core logic).
- **D064 (SDK Cleansing):** `run_rule()` moved to `core/rules.py`; `zenzic.rules` is now a 6-line re-export façade for backwards compatibility.
- **Why:** Enforce strict layer law. Core must never know about CLI. CLI owns orchestration.

### ADR-005: Z404 Agnostic Universalism (D087)

**[DECISION]** Z404 CONFIG_ASSET_MISSING extended from Docusaurus-only to all supported engines.

- **MkDocs:** Checks `theme.favicon` + `theme.logo` relative to `docs_dir/`.
- **Zensical:** Checks `[project].favicon` + `[project].logo`.
- **Why:** A Safe Harbor claiming engine-agnosticism cannot have Docusaurus-only integrity checks.

### ADR-006: Semantic Content Integrity — Frontmatter & Technical Blocks (D041/CEO-041)

**[DECISION]** YAML frontmatter, MDX comments `{/* */}`, and HTML comments `<!-- -->` are excluded from word count (Z502 short-content) but remain visible to the Shield (Z201).

- **Implementation:** `_visible_word_count()` in `scanner.py` strips these blocks locally (pure function, no mutation of the original text).
- **Why:** Frontmatter is system metadata, not prose. Counting it inflates Z502 word counts dishonestly. But frontmatter can contain real secrets (e.g., `custom_token: ghp_…`), so Shield must see it.
- **Security invariant:** Shield Pass 1A uses raw `enumerate(fh, start=1)` — no lines are ever skipped (ZRT-001 fix).

### ADR-007: Sovereign Sandbox (D043)

**[DECISION]** When the user provides an explicit `PATH` argument to `zenzic check all`, that path is the sovereign sandbox root — regardless of its position relative to the CWD repo root.

- **Implementation:** After computing `docs_root`, if `docs_root.relative_to(repo_root)` raises `ValueError`, reassign `repo_root = docs_root` in `check_all` (`cli/_check.py`).
- **Why:** Blood Sentinel's F4-1 guard (`_validate_docs_root`) was designed to block `docs_dir = "../../etc"` attacks in config files — not to block legitimate cross-project scanning. The user's explicit path is always intentional.

### ADR-008: Bilingual Structural Invariant (D045)

**[DECISION]** `docs/` (English) and `i18n/it/docusaurus-plugin-content-docs/current/` (Italian) must maintain perfect filesystem parity.

- **Atomic Moves:** Any `git mv` in EN must be accompanied by a matching `git mv` in IT in the same commit.
- **Why:** Language switcher in Docusaurus resolves paths by mirroring the English filesystem. A file present in EN but absent in IT causes a 404 on the switcher with no build-time warning.
- **Validation command:**

  ```bash
  diff <(find docs -name "*.mdx" | sed 's|^docs/||' | sort) \
       <(find i18n/it/docusaurus-plugin-content-docs/current -name "*.mdx" | \
         sed 's|^i18n/it/docusaurus-plugin-content-docs/current/||' | sort)
  ```

---

## [CHRONICLES] — Post-Mortem & Lessons Learned

### [BUG-001] Sentinel Friendly Fire (D043 — 2026-04-25)

- **ID:** BUG-001
- **Severity:** Showstopper (Exit 3 on legitimate operation)
- **Symptom:** Running `zenzic check all ../zenzic-doc` from inside `zenzic/` produced Blood Sentinel Exit 3.
- **Root Cause:** `_validate_docs_root` in `_shared.py` checked that `docs_root` was under `repo_root`. When the user provided `../zenzic-doc`, `_apply_target` set `config.docs_dir` to an absolute path. The guard correctly detected it was outside `repo_root` — but this was a false positive. The function confused the *location of the sandbox* with *escapes from the sandbox*.
- **[LESSON]** Blood Sentinel's F4-1 guard defends against malicious `docs_dir = "../../etc"` in config files. An explicit CLI `PATH` argument is always user-intentional and must be trusted as the new perimeter.
- **Permanent Fix:** In `check_all` (`cli/_check.py`), after computing `docs_root`, if it falls outside `repo_root`, reassign `repo_root = docs_root` (Rule R11 / ADR-007).
- **UI Fix:** Banner `print_header()` moved before path validation with guard `not quiet and output_format == "text"` so the banner always appears, even on fatal early exits.
- **Test:** `tests/test_cli.py::test_check_all_external_docs_root_not_blocked_by_sentinel`.

### [BUG-002] Blanket URL Exclusion Hiding Dead Links (D079 — 2026-04-22)

- **ID:** BUG-002
- **Severity:** Silent data corruption (3 broken links invisible to Sentinel)
- **Symptom:** `zenzic.toml` contained `excluded_external_urls = "https://zenzic.dev/"` — a blanket bypass added when the doc site was undeployed. After the Diátaxis restructure, three links in `README.md` silently rotted behind this curtain.
- **Dead links hidden:**
  - `/docs/usage/badges/` → correct: `/docs/how-to/add-badges/`
  - `/docs/guides/ci-cd/` → correct: `/docs/how-to/configure-ci-cd/`
  - `/docs/internals/architecture-overview/` → correct: `/docs/explanation/architecture/`
- **[LESSON]** Never use domain-level URL exclusions. Blanket exclusions create permanent blindspots. Use `--exclude-url <url>` at runtime for temporary skips. The `⚠ PERIMETER INVARIANT` comment in `zenzic.toml` documents that `docs_dir = "."` is a safety invariant keeping README inside the perimeter.
- **Permanent Fix:** Blanket exclusion removed; three links corrected.

### [BUG-003] Frontmatter Word Count Leak (D041/CEO-041 — 2026-04-24)

- **ID:** BUG-003
- **Severity:** Integrity failure (Z502 short-content check could be deceived)
- **Symptom:** A page with 100 lines of YAML frontmatter and the body word "LICENZE" would pass the Z502 minimum-word check, because frontmatter was counted as prose.
- **Root Cause:** `check_placeholder_content` passed raw text to word-count logic without stripping metadata blocks.
- **[LESSON]** Frontmatter, MDX comments `{/* */}`, and HTML comments `<!-- -->` are system metadata. They are never rendered to the user and must not inflate Z502 word counts. Separately, they CAN contain real secrets (e.g., `aws_key: AKIA…`), so the Shield must always scan them raw.
- **Permanent Fix:** `_visible_word_count()` in `scanner.py` strips these blocks locally (pure function, original text unchanged). Shield Pass 1A uses raw `enumerate` — no stripping applied before Shield (ZRT-001).

### [BUG-004] YAML Frontmatter Shield Blind Spot (ZRT-001 — 2026-04-15)

- **ID:** BUG-004
- **Severity:** CRITICAL (credential in YAML frontmatter invisible to Shield)
- **Symptom:** A secret in `custom_token: ghp_…` in frontmatter was not detected by the Shield.
- **Root Cause:** The content parsing loop used `_skip_frontmatter()` filtering before Shield, making frontmatter lines invisible to pattern scanning.
- **[LESSON]** Shield Pass must operate on raw file enumeration. Content passes (reference parsing, link harvesting) may skip frontmatter — Shield never may.
- **Permanent Fix:** Dual-stream architecture: Shield Pass 1A uses `enumerate(fh, start=1)` (raw, every line). Content Pass 1B uses `_iter_content_lines()` (filtered). `safe_read_line()` additionally guards every frontmatter line during metadata extraction.
- **Tests:** `TestShieldFrontmatterCoverage` in `tests/test_redteam_remediation.py`.

### [BUG-005] Z502 Pointer Targeting Frontmatter (D048 — 2026-04-25)

- **ID:** BUG-005
- **Severity:** UX failure (misleading diagnostic location)
- **Symptom:** `Z502 SHORT_CONTENT` finding had `line_no=1`, placing the red `❱` arrow at the opening `---` of YAML frontmatter. Users concluded frontmatter was being counted as prose (it was not — the pointer was just wrong).
- **Root Cause:** `check_placeholder_content` hardcoded `line_no=1` in the short-content `PlaceholderFinding`.
- **[LESSON]** A finding's line number is a contract with the user. Pointing at metadata noise (frontmatter `---`) erodes trust and causes false debugging sessions. Always point at the first line of actual content.
- **Permanent Fix:** `_first_content_line(text)` uses `_FRONTMATTER_RE.match()` to count newlines up to the end of the frontmatter block. The short-content finding now uses this as `line_no`.
- **Test:** `tests/test_scanner.py::test_short_content_pointer_skips_frontmatter`.

### [BUG-006] Z503 YAML Error Reports Relative Instead of Absolute Line (D048 — 2026-04-25)

- **ID:** BUG-006
- **Severity:** Precision failure (line-mapping error)
- **Symptom:** A YAML syntax error on line 3 of a snippet at file line 183 was reported as line 181 (fence line + 1) instead of 183 (fence line + 3).
- **Root Cause:** The YAML handler in `check_snippet_content` used `line_no=fence_line + 1` unconditionally, discarding the `exc.problem_mark.line` offset from the YAML parser. The Python handler correctly used `fence_line + exc.lineno`.
- **[LESSON]** Parity between language handlers. If Python extracts error line from the exception, YAML must too. Test all four handlers (Python, YAML, JSON, TOML) for absolute-line correctness.
- **Permanent Fix:** `offset = (mark.line + 1) if mark is not None else 1` where `mark = getattr(exc, "problem_mark", None)`. Line reported as `fence_line + offset`.
- **Test:** `tests/test_dual_mode.py::test_check_snippet_yaml_absolute_line_no`.

### [BUG-007] Caret `^^^^` Misaligns on Long Lines After Terminal Wrap (D048 — 2026-04-25)

- **ID:** BUG-007
- **Severity:** UX failure (surgical pointer becomes visual noise)
- **Symptom:** On Markdown files with very long link lines (200+ chars), the `^^^^` caret row was placed using col offsets from the original string length. Rich/terminal wraps the source line visually, so the carets appeared on the wrong visual row.
- **Root Cause:** `_render_snippet` used a hardcoded `col_start + caret_len <= 60` threshold — wrong constant, not terminal-aware, no source line truncation.
- **[LESSON]** Any diagnostic that renders visual pointers must account for terminal wrapping. The only robust approach: truncate the source line so it never wraps, then restrict carets to the visible portion.
- **Permanent Fix:** `shutil.get_terminal_size(fallback=(120, 24)).columns` determines `max_src`. Source lines longer than `max_src` are truncated with `…`. Carets only render when `col_start + caret_len <= max_src`.
- **Tests:** `tests/test_reporter.py::test_render_snippet_long_line_truncated`, `test_render_snippet_caret_suppressed_when_beyond_visible`.

### [BUG-008] Z503 YAML Multi-Document Raises False Positive (D048 — 2026-04-25)

- **ID:** BUG-008
- **Severity:** False positive (valid documentation rejected)
- **Symptom:** A YAML code block containing `---` (a document separator, common in Docusaurus frontmatter examples) raised "expected a single document in the stream but found another document".
- **Root Cause:** `yaml.safe_load(snippet)` only parses a single YAML document. Documentation tutorials legitimately show multi-document YAML (e.g., two frontmatter blocks as a comparison).
- **[LESSON]** Code snippet validators must not be stricter than the language specification. YAML officially supports multi-document streams. Rejecting `---` separators is a Zenzic-invented restriction that serves no security or quality purpose.
- **Permanent Fix:** `list(yaml.safe_load_all(snippet))` — accepts multi-document YAML. Generator consumed with `list()` to force full parse.
- **Test:** `tests/test_dual_mode.py::test_check_snippet_yaml_multi_doc_no_false_positive`.

### [BUG-009] Z903 Spurious Warnings on Engine Config Files (D050 — 2026-04-25)

- **ID:** BUG-009
- **Severity:** False positive (Z903 warning on infrastructure files)
- **Symptom:** Running `zenzic check all .` from the project root reported Z903 warnings on `docusaurus.config.ts`, `package.json`, and other toolchain files — the very files Zenzic reads to operate.
- **Root Cause:** `find_unused_assets()` performed no file-level system guardrail check. Any non-Markdown file in `docs_root` that was not referenced by a Markdown page was flagged as unused.
- **[LESSON]** A tool must never flag its own configuration inputs as quality issues. System guardrails for directories existed (`SYSTEM_EXCLUDED_DIRS`) but there was no equivalent for files. The asset scanner is not immune to the same noise it was designed to eliminate.
- **Permanent Fix:** Two-layer guardrail system (CEO-050). L1a: `SYSTEM_EXCLUDED_FILE_NAMES`/`SYSTEM_EXCLUDED_FILE_PATTERNS` in `models/config.py` — universal toolchain files. L1b: `BaseAdapter.get_metadata_files()` — adapter declares which engine config files it consumes. `LayeredExclusionManager` stores and applies both layers in `should_exclude_file()`. `find_unused_assets()` applies both layers inline before building the asset set.
- **Tests:** `tests/test_exclusion.py::TestSystemFileGuardrails`, `tests/test_scanner.py::test_find_unused_assets_skips_system_infrastructure_files`, `tests/test_scanner.py::test_find_unused_assets_skips_adapter_metadata_files`.

---

## [SPRINT LOG] — CEO Directive History

### D036 — Finding Code Mapping

Codified all diagnostics into `Zxxx` scheme. `codes.py` created as single source of truth.

### D037 — Standalone Renaissance

`VanillaAdapter` → `StandaloneAdapter`. Breaking change: `engine = "vanilla"` raises `ConfigurationError [Z000]`.

### D038 — Final Audit Record

CHANGELOG.md, CHANGELOG.it.md, RELEASE.md updated for Breaking Change + Zxxx introduction + Lab menu.

### D039 — The Guardrail Lifecycle

`_factory.py` migration guard annotated, `[Z000]` prefix added. TODO comment later removed in v0.7.0 (D "Codebase Parity" sprint) but guard itself is permanent.

### D040 — Institutional Memory

`.github/copilot-instructions.md` created as canonical agent briefing document.

### D055 (CEO) — Sovereign CLI

`zenzic.integrations.mkdocs` plugin removed. Zenzic becomes pure Sovereign CLI.

### D061-B/D068 (CEO) — Inspect Renaming

`zenzic plugins` command removed. Replaced by `zenzic inspect capabilities`.

### D062-B — Core Law Enforcement

`src/zenzic/ui.py` → `src/zenzic/core/ui.py`. Core must never import upward.

### D063 — Lab Relocation

`src/zenzic/lab.py` → `src/zenzic/cli/_lab.py`. Lab is CLI orchestration, not core logic.

### D064 — SDK Cleansing

`run_rule()` moved to `core/rules.py`. `zenzic.rules` becomes 6-line re-export façade.

### D066 — Physical Purge

`src/zenzic/integrations/` directory deleted entirely. No ghost files remain.

### D076/D077/D078/D079 — Obsidian Integrity Sprint

**Version:** 0.7.0 · **Date:** 2026-04-22

- D076: README Perimeter Invariant (`docs_dir = "."` safety comment).
- D077: Z104 Proactive Suggestion Engine (`difflib.get_close_matches`, cutoff 0.6).
- D078: Standalone Truth Audit — Z402 disabled without nav contract explicitly documented.
- D079: Blanket URL exclusion removed; 3 dead Diátaxis links corrected. See BUG-002.

### D082–D086 — Obsidian Mirror Pass

**Version:** 0.7.0 · **Date:** 2026-04-22

Z404 for Docusaurus. Lab Obsidian Seal. zenzic-doc GitHub release workflow. Favicon/OG meta tag fixes. Lab Acts 0–10 (11 acts).

### D087 (CEO) — The Agnostic Universalism

**Version:** 0.7.0 · **Date:** 2026-04-22

Z404 extended to MkDocs + Zensical. `cli/_check.py` multi-engine dispatch. See ADR-005.

### D092 (CEO) — SARIF 2.1.0 Export

**Version:** 0.7.0

`--format sarif` on all check commands. GitHub Code Scanning native integration.

### D093 (CEO) — Cross-Platform CI Matrix

**Version:** 0.7.0

3×3 matrix: `[ubuntu, windows, macos]` × `[3.11, 3.12, 3.13]`. `fail-fast: false`.

### D094 (CEO) — Official GitHub Action

**Version:** 0.7.0

`PythonWoods/zenzic-action` composite action created. See zenzic-action repo.

### D109–D116 — Typography, Navigation & Layout Polish

**Version:** 0.7.0 · **Date:** 2026-04-22

Visual polish sprint for zenzic-doc: Geist + JetBrains Mono, navigation arrows, responsive layout.

### D117 — `pathname:` Protocol Support

**Version:** 0.7.0 · **Date:** 2026-04-22

`validator.py` recognises `pathname:///` scheme (Docusaurus static assets). No false-positive Z101 for Docusaurus engine.

### D118–D119 — Blog Title Consistency & Sibling Release Protocol

**Version:** 0.7.0 · **Date:** 2026-04-22

Blog `h2 a` colors locked. RELEASE.md rewritten as Sibling Release Protocol. `just bump` recipe + `scripts/bump-version.sh`.

### D122 — Governance Pack

**Version:** 0.7.0 · **Date:** 2026-04-22

`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff`, `SECURITY.md` created in zenzic-doc. REUSE compliant.

### D123–D125 — Global Brand Sync

**Version:** 0.7.0 · **Date:** 2026-04-22

`@site/` alias expansion (D123). Multi-root path resolution (D124). Mandatory i18n anchor integrity (D125). READMEs: wordmark-only, no Roadmap, Chronicles added.

### D127 (CEO) — The Sovereign Identity Protocol

**Version:** 0.7.0 · **Date:** 2026-04-22

X.com / Twitter links removed. Italian flag 🇮🇹 restored. Social links: GitHub + Journal only.

### D "Codebase Parity" Sprint — 2026-04-24

- Z000 guard promoted to permanent (TODO comment deleted, guard stays).
- `case_sensitive_exists()` added for Windows / macOS case-insensitive filesystem parity.
- `_visible_word_count()` strips MDX + HTML comments + frontmatter. See BUG-003.
- Documentation parity: 13 `VanillaAdapter` → `StandaloneAdapter` refs, Z000 JSON contract documented.
- CVE-2026-3219: pip polyglot archive — mitigated; Zenzic uses `uv` only.

### D "Mutation Testing Sprint" — 2026-04-24

29 tests in `test_cache.py`, 12 in `test_reporter.py`. `TestToCanonicalUrlMutantKill` (15 tests), `TestObfuscateSecretMutantKill` (7 tests). Mutmut on `rules.py`, `shield.py`, `reporter.py`. 86.7% mutation score (target 75%).

### D042 (CEO) — The Perpetual Memory Protocol

**Version:** 0.7.0 · **Date:** 2026-04-25

Memory Law (section 9) codified in all `.github/copilot-instructions.md` files. Sprint not closed until knowledge is documented here.

### D043 (CEO) — The Sentinel's Sanity Pass

**Version:** 0.7.0 · **Date:** 2026-04-25

Blood Sentinel false positive fixed (see BUG-001). Rule R11 added. Banner hoisted before validation.

### D045 (CEO) — Codifying the Symmetry

**Version:** 0.7.0 · **Date:** 2026-04-25

Law of Italian Mirroring codified. Rule R12 added. Symmetry audit confirms zero asymmetries.

### D046 (CEO) — The Knowledge Refactoring

**Version:** 0.7.0 · **Date:** 2026-04-25

Obsidian Ledger schema adopted for all three repo agent instructions. Audit of changelogs, code, and docs completed before writing.

### D047 (CEO) — The Knowledge Trinity

**Version:** 0.7.0 · **Date:** 2026-04-25

Confirmed: Riscrittura completa (Option 1 — Obsidian Ledger full rewrite) for all three repos. zenzic-action receives its first `.github/copilot-instructions.md`.

### D049 (CEO) — The Obsidian Memory Law

**Version:** 0.7.0 · **Date:** 2026-04-25

`[CLOSING PROTOCOL]` section added to all three repo agent instruction files immediately after `[MANIFESTO]`. Memory Law in `[POLICIES]` upgraded to "The Custodian's Contract" — Class 1 violation clause, explicit per-repo closure checklists. System resolves the "Paradosso del Custode senza Memoria".

### D048 (CEO) — The Precision Polish

**Version:** 0.7.0 · **Date:** 2026-04-25

Four precision bugs fixed. **BUG-005** (Z502 pointer at frontmatter — `line_no=1` → `_first_content_line()`). **BUG-006** (Z503 YAML relative line — `fence_line+1` → `fence_line+problem_mark.line+1`). **BUG-007** (Z105/Z503 caret misalignment on wrapped lines — terminal-width-aware truncation with `…` suffix). **BUG-008** (Z503 YAML multi-document — `safe_load` → `safe_load_all`). Five regression tests added. 1201 passing.

### D050 (CEO) — The Intelligent Perimeter

**Version:** 0.7.0 · **Date:** 2026-04-25

**BUG-009** fixed: Z903 false positives on engine config and infrastructure files. Two-layer guardrail system: L1a (`SYSTEM_EXCLUDED_FILE_NAMES`/`SYSTEM_EXCLUDED_FILE_PATTERNS` in `models/config.py`) shields universal toolchain files; L1b (`BaseAdapter.get_metadata_files()`) lets each adapter declare its own config files. `LayeredExclusionManager` stores and applies both layers. `find_unused_assets()` enforces both inline. Rule R13 codified. 7 regression tests added. 1208 passing.
