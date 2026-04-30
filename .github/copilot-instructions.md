<!-- Sovereign Memory Master. Mirror: .github/copilot-instructions.md -->
# 🛡️ ZENZIC CORE — Zenzic Ledger v0.7.0 "Quartz Maturity"

> **Single Source of Truth for all agents and contributors.**
> Schema: [MANIFESTO] → [POLICIES] → [ARCHITECTURE] → [ADR] → [ACTIVE SPRINT] → [ARCHIVE LINK]

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

### Step 0 — Pre-Task Alignment

- [ ] Read the **[POLICIES]** section of this ledger before starting any work.
- [ ] The **Law of Contemporary Testimony (CEO-059)** applies unconditionally: code and documentation are a single indivisible unit. No task is complete until both are aligned.

### Step 1 — Update This File

- [ ] New architectural facts? → Update **[ARCHITECTURE]**
- [ ] New decisions made? → Add an **[ADR]** entry (tagged `[DECISION]`)
- [ ] Bug found and fixed? → Promote the lesson to a **[POLICY]** rule or **[ADR]** (permanent invariants only). Update **[ACTIVE SPRINT]**.
- [ ] Sprint complete? → Update **[ACTIVE SPRINT]**. Purge previous-sprint entry to `CHANGELOG.md`.
- [ ] **Size Guardrail:** This file exceeds 400 lines? → Trigger a curation task (Law of Evolutionary Curation).

### Step 2 — Update Changelogs

- [ ] `CHANGELOG.md` — add sprint section under current version heading
- [ ] `CHANGELOG.it.md` — Italian translation of the same section
- [ ] `RELEASE.md` — keep concise and marketing-ready (max 200 lines — Law of Executive Brevity)
- [ ] **Archive Check:** If `CHANGELOG.md` exceeds 500 lines → move pre-v0.6.0 versions to `CHANGELOG.archive.md` (Sentinel Archive Protocol).
- [ ] **Executive Filter:** Review `RELEASE.md`. Technical fluff (mutation tables, internal bug IDs, CVE traces) belongs in `CHANGELOG.md` or `explanation/architecture.mdx` — not in the release notes.

### Step 3 — Staleness & Testimony Audit

- [ ] `README.md` / `README.it.md` — check: version numbers, feature lists, CLI flag examples, Z-code table, architecture descriptions
- [ ] **Contemporary Check (CEO-059):**
  - Changed a CLI flag or command signature? → Update `reference/cli.mdx` (EN + IT) in zenzic-doc
  - Changed a default value or config option? → Update `reference/configuration.mdx` (EN + IT) in zenzic-doc
  - Fixed an architectural bug? → Update `explanation/architecture.mdx` (EN + IT) in zenzic-doc
  - Changed a finding code, threshold, or message? → Update `reference/finding-codes.mdx` (EN + IT) in zenzic-doc
  - Adapter discovery or engine config behavior changed? → Update `how-to/configure-adapter.mdx` (EN + IT) in zenzic-doc
- [ ] **Precedence Table:** New CLI flags are reflected in the Configuration Priority section of `reference/configuration.mdx` (EN + IT).
- [ ] **Bilingual Mirroring:** Every EN doc update has a matching IT update in the same commit.
- [ ] Coordinate with zenzic-doc repo for any `.mdx` updates required (see Law of Contemporary Testimony)

### Step 4 — Verification Gate

- [ ] Full test suite: `nox -s tests`
- [ ] Self-audit: `zenzic check all` on this repo (exit 0 required)
- [ ] Stage and review the full diff before committing

---

## [POLICIES] — Immutable Operational Laws

### The Law of Contemporary Testimony [MANDATORY] — CEO-059

- **[INVARIANT] Code and Documentation are a single, indivisible unit of work.**
  - **No Silent Logic:** Any change in CLI behavior, flags, findings, or configuration priority MUST be reflected in the relevant `.mdx` and `README` files within the SAME sprint/task.
  - **Verification:** An agent is NOT permitted to signal "Task Complete" if the documentation reflects old behavior.
  - **Sovereignty:** Before starting ANY task, the agent MUST read this ledger. This file is the only source of truth for current project policies.

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
- **[RULE R14] Portability is Execution-Independent (CEO-053).** [DECISION] Absolute links (starting with `/`) are hard errors (Z105) unconditionally — even if the target file exists on disk and is reachable locally. Z105 is a pre-resolution gate: the validator must fire it before any filesystem check. Rationale: an absolute link breaks portability when the site is hosted in a subdirectory. The fact that the file exists on the author's machine is irrelevant.
- **[RULE R15] Scope Integrity (CEO-054).** [DECISION] A resolved link is valid only if its target is within the engine's permitted perimeter: `docs_root` + adapter-declared static directories. File existence on the host filesystem outside this perimeter is irrelevant — the Shield resolver (PathTraversal Z202) enforces this unconditionally. `find_repo_root(search_from=target)` (CEO-052) ensures the perimeter is anchored to the correct project when invoked remotely. Corollary: `excluded_dirs` must **not** include directory names that contain files actively referenced by Markdown pages (e.g. `assets/`), as excluding them from the walk breaks the asset index and causes Z104 false positives.
- **[RULE R16] Protocol Awareness (CEO-055).** [DECISION] The `pathname:///` protocol is the Docusaurus "Diplomatic Courier" — a Docusaurus-specific static-asset escape hatch. In Docusaurus mode, `pathname:///assets/file.html` parses to `scheme="pathname"`, `path="/assets/file.html"` and the leading `/` is a URI convention artifact — not an absolute-path violation. The Z105 gate is conditioned on `not (parsed.scheme == "pathname" and engine == "docusaurus")`. In all other engines (MkDocs, Zensical, Standalone), `pathname:///` is unrecognized and triggers Z105 normally. Corollary: word-count stripping (Z502) must strip MDX/HTML comments **before** running the frontmatter regex — MDX files often open with a `{/* SPDX … */}` header before the `---` block, which prevents `_FRONTMATTER_RE` (anchored to `\A`) from matching unless the comment is removed first.
- **[RULE R17] CLI Symmetry (CEO-056).** [DECISION] `zenzic score [PATH]` and `zenzic diff [PATH]` accept an optional positional `PATH` argument — identical sovereign root semantics as `zenzic check all [PATH]`. `find_repo_root(search_from=target)` is called unconditionally when `PATH` is provided: configuration follows the target, not the caller (ADR-009). The banner is printed immediately before analysis, not after. `diff` automatically derives the snapshot path from `repo_root`, not CWD.
- **[RULE R18] Total CLI Symmetry (CEO-060).** [DECISION] Every filesystem-interacting CLI command (except `lab` and `inspect`) accepts an optional positional `PATH` argument with sovereign root semantics identical to `check all`. `find_repo_root(search_from=target)` is called when PATH is provided; `_apply_target()` recalibrates `docs_root` and loads the target's config. For `init`, PATH is treated as the `repo_root` directly (Genesis Nomad): the directory is created with `mkdir(parents=True, exist_ok=True)` if absent. The active configuration (engine, docs_dir, exclusions) always follows the target repository, never the caller's CWD.
- **[RULE R19] No Domain-Level URL Exclusions.** `excluded_external_urls` in `zenzic.toml` must target specific URLs, not entire domains (e.g. `"https://zenzic.dev/"`). A domain blanket exclusion creates permanent blindspots that survive content restructures. Use `--exclude-url <url>` at CLI runtime for temporary skips only.

- **[RULE R20] Machine Silence (D077).** Any machine-readable output format (`json` or `sarif`) mandates the total suppression of Rich banners, headers, and informational panels on stdout. Machine streams must remain 100% valid against their schema. **Implementation:** `_print_no_config_hint(output_format)` gates internally on `_MACHINE_FORMATS = frozenset({"json", "sarif"})`; `print_header()` is gated at each call site with `if ... and output_format == "text"`. No Rich output may reach stdout when a machine is reading.

- **[RULE R21] Protocol Sovereignty (D080).** The Core (`validator.py`, `scanner.py`) must never hardcode engine names (`"docusaurus"`, `"mkdocs"`, etc.) as conditions for validation logic. Engine-specific behaviour must be declared in the adapter (`BaseAdapter` protocol method) and queried by the Core. **Implementation:** `BaseAdapter.get_link_scheme_bypasses() -> frozenset[str]` is the canonical pattern. If the Core must behave differently per engine, add a `get_*()` method to the protocol — never add `if engine == "x"` to Core logic.

- **[RULE R22] Fall-before-Redemption (D081).** Tutorial and onboarding content must show the broken state first (The Siege), explain the fix, then show the passing state (the Sigillo della Sentinella). The emotional contrast is the lesson — a green exit means nothing without the memory of the breach. **Implementation:** `first-audit.mdx` Step 2 uses `uvx zenzic lab 2` (leaked credential) as the Siege, then `uvx zenzic lab 0` as the Shield. The `examples/matrix/red-team/` fixtures are the canonical broken state; `examples/matrix/blue-team/` is the canonical fixed state.

- **[RULE R23] The Sentinel's Filter (CEO-137).** A rule ships in the Quartz Core if and only if it defends one of three dimensions: **(1) Structural Integrity** — prevents a broken user experience (broken links, orphan pages, missing indices); **(2) Hardened Security** — protects infrastructure or secrets (Shield Z201, Blood Sentinel Z202/Z203); **(3) Technical Accessibility** — ensures third-party tools can consume the source (Z505 Untagged Code Blocks, Z503 Snippet Errors, Z403 Alt Text, Z106 Circular Link). Rules that address prose aesthetics — line length, list style, spelling, terminology consistency — are permanently out of scope. This is not a limitation; it is a mandate. The Sentinel enforces structure. Everything else is editorial sovereignty. **Documentation:** `docs/explanation/structural-integrity.mdx` (EN + IT).

- **[RULE R24] Zero-Amnesia Law (CEO-243).** No commit shall be merged into `main` if the `[CODE MAP]` does not perfectly reflect the current AST of the source code. **Enforcement:** `just verify` is the only authorised local gate and enforces automatic memory synchronisation via `just brain-map` → `uv run zenzic brain map .` before every preflight run. **Implementation:** `src/zenzic/core/cartography.py` (pure AST scanner) + `src/zenzic/cli/_brain.py` (orchestration + Zone B audit + Trinity Mesh + Master-Shadow Sync). **Note on numbering:** CEO-243 requested "Rule 17" — R17 was already occupied (CLI Symmetry CEO-056). This was surfaced per the Sovereign Memory Law (CEO-183) and the CEO ratified R24 as the correct slot.

- **[INVARIANT] Public-facing files (`RELEASE.md`, `README.md`) are for humans and decision makers — not for implementation audit trails.**
  - **Technical Dump Prohibited:** Mutation testing tables, internal bug IDs, forensic traces, and CVE details do not belong in `RELEASE.md`. They belong in `CHANGELOG.md`, `CHANGELOG.archive.md`, or internal ADRs.
  - **Archival Trigger:** When `CHANGELOG.md` exceeds 500 lines, move pre-v0.6.0 versions to `CHANGELOG.archive.md` (the **Sentinel Archive Protocol**). Add an archive link in the preamble. The main changelog covers only the current major cycle.
  - **Summarization:** Every 5 technical sprints are summarized into 1 executive highlight in `RELEASE.md`. Sprint-level granularity lives in `CHANGELOG.md`.
  - **Line Budget:** `RELEASE.md` ≤ 200 lines. If it exceeds this, apply the Executive Filter (see CLOSING PROTOCOL Step 2).

### Documentation Law — The Quartz Testimony [MANDATORY]

- **[INVARIANT] Every behavioral or structural change to the codebase must be reflected in the corresponding `.mdx` documentation before the sprint is closed.** A code change without a documentation update is a ghost commit — it alters reality without updating the map.
- **Trigger rules (mandatory — not optional):**
  - I/O signature, config options, or exclusion logic changed → Update `reference/configuration.mdx` (EN + IT) in zenzic-doc
  - UI output, CLI flags, or module structure changed → Update `explanation/architecture.mdx` (EN + IT) in zenzic-doc
  - A `Zxxx` finding changed (threshold, message, line accuracy, or semantic scope) → Update `reference/finding-codes.mdx` (EN + IT) in zenzic-doc
  - Adapter discovery or engine config handling changed → Update `how-to/configure-adapter.mdx` (EN + IT) in zenzic-doc
- **Enforcement:** The [CLOSING PROTOCOL] Step 3 (Staleness & Testimony Audit) implements this law. **A sprint without a Testimony check is not closed.**

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
| Z1xx | Link Integrity | Z101 LINK_BROKEN, Z102 ANCHOR_MISSING, Z103 UNREACHABLE_LINK, Z104 FILE_NOT_FOUND, Z105 ABSOLUTE_PATH, Z106 ALT_TEXT_MISSING, Z107 CIRCULAR_ANCHOR |
| Z2xx | Security | Z201 SHIELD_SECRET, Z202 PATH_TRAVERSAL, Z203 PATH_TRAVERSAL_SUSPICIOUS |
| Z3xx | Reference Integrity | Z301 DANGLING_REF, Z302 DEAD_DEF, Z303 CIRCULAR_LINK |
| Z4xx | Structure | Z401 MISSING_DIRECTORY_INDEX, Z402 ORPHAN_PAGE, Z403 SNIPPET_UNREACHABLE, Z404 CONFIG_ASSET_MISSING |
| Z5xx | Content Quality | Z501 PLACEHOLDER, Z502 SHORT_CONTENT, Z503 SNIPPET_ERROR, Z504 QUALITY_REGRESSION, Z505 UNTAGGED_CODE_BLOCK |
| Z9xx | Engine / System | Z901 RULE_ERROR, Z902 RULE_TIMEOUT, Z903 UNUSED_ASSET, Z904 DISCOVERY_ERROR, Z905 BRAND_OBSOLESCENCE, Z906 NO_FILES_FOUND |

### Adapter Identity Rules

- `"standalone"` — canonical name for projects with no build config. Uses `StandaloneAdapter`. In Standalone Mode, orphan detection (Z402) is disabled (no navigation contract).
- `"vanilla"` — **permanently removed** in v0.6.1. Any usage raises `ConfigurationError [Z000]`.
- `"auto"` — default engine value in `ZenzicConfig`. Resolved at runtime by `discover_engine(repo_root)` in `_factory.py`. Priority: zensical.toml → docusaurus.config.ts/js → mkdocs.yml → `"standalone"`. Never stored as a cache key — resolved before lookup.
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
8. **Chronicles position:** Zenzic Chronicles section always precedes the footer.

### Memory Law — The Custodian's Contract

- **[INVARIANT] The [CLOSING PROTOCOL] is a non-negotiable Engineering Contract.**
  An agent that ends a session without completing it commits a Class 1 violation (Technical Debt). The successor inherits a ghost, not a project.
- **[INVARIANT] This file is the agent's only persistent memory.** Update it before the final commit — not after.
- **[INVARIANT] Definition of Done:** A sprint is not closed until CHANGELOG is current, RELEASE.md passes the Executive Filter (≤ 200 lines), and the staleness audit is complete.
- **[INVARIANT] Proactivity:** Agents must notify the Tech Lead when a code change contradicts or expands current guidelines.
- **[INVARIANT] Sovereignty:** This file is the single source of truth for agent behavior.

### The Sovereign Memory Law [MANDATORY] — CEO-183

- **[INVARIANT] This ledger is the project's external cortex.** Agents must use it to challenge human directives that conflict with established invariants before executing them.
- **Mechanism:** Before executing any directive touching established architecture, the agent checks the ledger for invariant conflicts. If found, the conflict is surfaced to the human before proceeding. The human decides. The ledger records the outcome.
- **Historical record:** Sprint D091 — the CEO issued a directive to reuse engine name `"vanilla"`. ADR-002 (permanent Z000 guard) was in the ledger. The agent declined. The CEO's earlier self corrected the CEO's current self. The ledger worked.

### The Law of Proactive Execution [MANDATORY] — CEO-175

- **[INVARIANT] Agents proceed on unambiguous tasks without waiting for step-by-step confirmation.** When the task is clear and reversible, implement first, report after.
- **[INVARIANT] When a design decision has ambiguities, propose a concrete solution and state the assumption explicitly. Implement, then document the choice.**
- **[RULE]** Raise questions BEFORE starting work only when a wrong design decision would require significant rework that cannot be easily undone.
- **Corollary — Score vs. Gate Separation (CEO-175):** The Score (computed metric) and the `fail_under` threshold (enforcement policy) are independent but synchronized. Category caps bound the metric to prevent noise from masking signal; they do not weaken the gate. A score of 70/100 with `fail_under = 80` still exits 1.

### The Law of Evolutionary Curation [MANDATORY] — D073

- **[INVARIANT] This file is a Working Context, not a historical archive.**
  - **Policy Conversion:** When a bug's solution becomes a permanent invariant, distill it into a **[POLICY]** rule or **[ADR]** entry. The verbose post-mortem belongs in `CHANGELOG.md`.
  - **Sprint Purge:** `[ACTIVE SPRINT]` holds only the current sprint and the last closed sprint. Older history is purged to `CHANGELOG.md`.
  - **Size Guardrail:** If this file exceeds 400 lines, the agent MUST trigger a curation task before closing the sprint.

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
    _lab.py                 — lab command: 20 Acts (0–19), interactive showcase
    _standalone.py          — standalone commands: diff, init, score
    _shared.py              — shared helpers: _build_exclusion_manager, _validate_docs_root, _ui, console
    _brain.py               — brain sub-app: map command + Zone B audit + Trinity Mesh + shadow sync (dev-only, CEO-242)
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
    cartography.py          — Sovereign Cartographer: pure AST scanner (CEO-242); scan_python_sources, render_markdown_table, update_ledger
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
    ui.py                   — SentinelPalette, SentinelUI, make_banner (moved here in D062-B)
  models/
    config.py               — ZenzicConfig / BuildContext (Pydantic); 4-level config priority
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

**Config priority (4 levels):** CLI flags > `zenzic.toml` > `[tool.zenzic]` in `pyproject.toml` > built-in defaults. CLI flags always win.

---

## [CODE MAP] — Indice Rapido Moduli

> Auto-generato da `scripts/map_project.py` via AST (CEO-083 — Sentinel Mapper Protocol).
> Aggiornare con `just map-update` dopo ogni modifica a `src/`.

<!-- MAP_START -->
### Module Quick Index

> Auto-generated by `zenzic brain map` via AST (CEO-242 — Sovereign Cartographer).
> Update with `just brain-map` after any change to `src/`.

| File | Classes | Public Functions | Note |
|------|---------|-----------------|------|
| `cli/_brain.py` | — | `brain_map` | brain sub-commands — Developer Sovereign Cartography tools. |
| `cli/_check.py` | — | `check_links`, `check_orphans`, `check_snippets`, `check_references`, `check_assets`, `check_placeholders`, `check_all` | Check sub-commands: links, orphans, snippets, references, assets, placeholders, all. |
| `cli/_clean.py` | — | `clean_assets` | Clean sub-commands: safely remove unused documentation files. |
| `cli/_inspect.py` | — | — | Inspect sub-commands: introspect the Zenzic scanner arsenal and plugin registry. |
| `cli/_lab.py` | — | `parse_act_range`, `lab` | ``zenzic lab`` — interactive showcase of bundled documentation examples. |
| `cli/_shared.py` | — | `configure_console`, `get_ui`, `get_console` | Shared CLI infrastructure: console singleton, _ui gateway, and cross-command utilities. |
| `cli/_standalone.py` | — | `score`, `diff`, `init` | Standalone commands: score, diff, init — and their private helpers. |
| `core/adapter.py` | — | — | Backwards-compatible alias for ``zenzic.core.adapters``. |
| `core/adapters/_base.py` | `RouteMetadata`, `BaseAdapter` | — | BaseAdapter Protocol — the engine-agnostic contract every adapter must satisfy. |
| `core/adapters/_docusaurus.py` | `DocusaurusAdapter` | `find_docusaurus_config`, `check_config_assets` | DocusaurusAdapter — adapter for Docusaurus v3 with native i18n support. |
| `core/adapters/_factory.py` | — | `discover_engine`, `list_adapter_engines`, `clear_adapter_cache`, `get_adapter` | Adapter factory — dynamic entry-point discovery with StandaloneAdapter fallback. |
| `core/adapters/_mkdocs.py` | `MkDocsAdapter` | `find_config_file`, `check_config_assets` | MkDocsAdapter — adapter for MkDocs folder-mode and suffix-mode i18n. |
| `core/adapters/_standalone.py` | `StandaloneAdapter` | — | StandaloneAdapter — no-op adapter for projects with no recognised build engine. |
| `core/adapters/_utils.py` | `FileMetadata` | `case_sensitive_exists`, `remap_to_default_locale`, `extract_frontmatter_slug`, `extract_frontmatter_draft`, `extract_frontmatter_unlisted`, `extract_frontmatter_tags`, `build_metadata_cache` | Shared utilities for Zenzic adapters. |
| `core/adapters/_zensical.py` | `ZensicalLegacyProxy`, `ZensicalAdapter` | `find_zensical_config`, `check_config_assets` | ZensicalAdapter — native adapter for the Zensical build engine. |
| `core/cache.py` | `CacheManager` | `make_content_hash`, `make_config_hash`, `make_vsm_snapshot_hash`, `make_file_key` | Content-addressable cache for Zenzic rule results. |
| `core/cartography.py` | `ModuleInfo` | `scan_python_sources`, `render_markdown_table`, `update_ledger` | Sovereign Cartographer — AST-based module mapper for AI context generation. |
| `core/codes.py` | `ZenzicExitCode`, `CoreScanner` | `get_sarif_name`, `normalize`, `label` | Zenzic Finding Code Registry. |
| `core/discovery.py` | — | `walk_files`, `iter_locale_markdown_sources`, `iter_markdown_sources` | Centralised file-discovery utilities for the Zenzic Core. |
| `core/exceptions.py` | `ZenzicError`, `ConfigurationError`, `EngineError`, `CheckError`, `NetworkError`, `PluginContractError` | — | Core exception hierarchy for Zenzic. |
| `core/exclusion.py` | `VCSIgnoreParser`, `LayeredExclusionManager` | — | Layered Exclusion system: VCS-aware file exclusion with 4-level hierarchy. |
| `core/logging.py` | — | `get_logger`, `setup_cli_logging` | Logging configuration for Zenzic. |
| `core/models.py` | — | — | Re-export shim — canonical location is ``zenzic.models.references``. |
| `core/reporter.py` | `Finding`, `SentinelReporter` | — | Sentinel Report Engine — Ruff-inspired CLI output for Zenzic. |
| `core/resolver.py` | `PathTraversal`, `FileNotFound`, `AnchorMissing`, `Resolved`, `InMemoryPathResolver` | — | Pure in-memory path resolver for Markdown documentation link validation. |
| `core/rules.py` | `ResolutionContext`, `RuleFinding`, `Violation`, `BaseRule`, `CustomRule`, `AdaptiveRuleEngine`, `CircularAnchorRule`, `UntaggedCodeBlockRule`, `BrandObsolescenceRule`, `VSMBrokenLinkRule`, `PluginRuleInfo`, `PluginRegistry` | `list_plugin_rules`, `run_rule` | Zenzic Rule Engine — pluggable, pure-function linting rules. |
| `core/scanner.py` | `PlaceholderFinding`, `ReferenceScanner` | `find_repo_root`, `calculate_orphans`, `check_placeholder_content`, `check_asset_references`, `calculate_unused_assets`, `find_orphans`, `find_placeholders`, `find_unused_assets`, `find_missing_directory_indices`, `check_image_alt_text`, `scan_docs_references` | Filesystem scanning utilities: repo root discovery, orphan page detection, |
| `core/scorer.py` | `CategoryScore`, `ScoreReport` | `compute_score`, `save_snapshot`, `load_snapshot` | Documentation quality scoring engine. |
| `core/shield.py` | `SecurityFinding`, `ShieldViolation` | `scan_url_for_secrets`, `scan_line_for_secrets`, `scan_lines_with_lookback`, `safe_read_line` | Zenzic Shield: secret-detection engine integrated into the Pass 1 harvesting phase. |
| `core/ui.py` | `SentinelPalette`, `SentinelUI` | `emoji`, `make_banner`, `make_sentinel_header` | Sentinel Visual Identity — SentinelPalette, terminal detection, and UI helpers. |
| `core/validator.py` | `LinkInfo`, `SnippetError`, `LinkError`, `LinkValidator` | `extract_links`, `slug_heading`, `anchors_in_file`, `extract_ref_links`, `validate_links_async`, `generate_virtual_site_map`, `check_nav_contract`, `validate_links`, `validate_links_structured`, `check_snippet_content`, `validate_snippets` | Validation logic: native link checking (internal + external) and snippet checks. |
| `main.py` | — | `cli_main` | Entry point for the zenzic CLI application. |
| `models/config.py` | `CustomRuleConfig`, `ProjectMetadata`, `BuildContext`, `ZenzicConfig` | — | Zenzic configuration models and generator detection. |
| `models/references.py` | `ReferenceMap`, `ReferenceFinding`, `IntegrityReport` | — | Data models for the Two-Pass Reference Pipeline. |
| `models/vsm.py` | `Route` | `build_vsm` | Virtual Site Map (VSM) data model. |
| `rules.py` | — | — | Public Plugin SDK — import from here in your plugin code. |
<!-- MAP_END -->

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
- **Order invariant (BUG-012):** MDX and HTML comments must be stripped **before** running the `_FRONTMATTER_RE` regex (anchored to `\A`). Comment blocks before `---` prevent the regex from matching; stripping them first is load-bearing.
- **Corollary (BUG-014 — D072):** `_first_content_line()` applies the same three-phase skip (HTML comments → frontmatter → blank lines) so the Z502 `❱` pointer lands on the first prose word, not on a REUSE SPDX licence header.

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

### ADR-009: Path Sovereignty (CEO-052)

**[DECISION]** "The configuration follows the target, not the caller." When an explicit `PATH` argument is provided to `zenzic check all`, `find_repo_root()` must search upward from that path — not from `os.getcwd()`. The active repo configuration (engine, `docs_dir`, exclusions) is always determined by the repository that owns the target, never by the working directory of the invoking shell. This invariant prevents "Context Hijacking": running Zenzic from repo A pointing at repo B must load B's `zenzic.toml` exclusively.

- **Implementation:** `find_repo_root(search_from=target_path)` parameter in `core/scanner.py`. `check_all()` in `cli/_check.py` derives `search_from` from the resolved target before calling `find_repo_root`. `_apply_target()` sovereign root guard: when `target == repo_root`, `docs_dir` is preserved from config rather than overridden to `"."`.

---

### ADR-010: Range-Aware Showroom Commands (D069)

**[DECISION]** Showcase commands (like `zenzic lab`) must accept range syntax (`N-M`) in addition to single integers and named shorthands (`all`), so operators can run thematic groups of acts in one invocation without scripting loops.

- **Implementation:** Argument type changed from `int` to `str`. `parse_act_range(raw: str) -> list[int]` is a pure function (no side effects, no I/O) that handles single integers, inclusive ranges, and `"all"`. It raises `ValueError` for malformed input; the caller catches and renders an `SentinelUI.print_exception_alert()` panel.
- **Rule R18 — Range Awareness:** Showroom commands should support range syntax (N-M) to facilitate batch demonstration and testing without requiring shell scripting by the operator.
- **Why:** The `zenzic lab` menu explicitly mentions `zenzic lab 11–16` in its footer hint. Shipping a command that advertises a capability it doesn't support is a false promise — a violation of the Maturity Contract.

### ADR-011: Quartz Weight Matrix — 4-Category Scoring (CEO-149)

**[DECISION]** `compute_score()` refactored from 5 implicit categories to 4 named, weighted categories with security override.

- **Categories:** `structural` (40%) = Z101/Z102/Z104/Z105/Z107; `content` (30%) = Z501/Z502/Z503/Z505; `navigation` (20%) = Z402; `brand` (10%) = Z903/Z904/Z905.
- **Security override:** If `security_violations > 0` (any Z2xx), `ScoreReport.score = 0` and `security_override = True` unconditionally. A leaking credential cannot receive a score.
- **Z904 scored:** Nav contract errors now contribute to the `brand` category instead of being non-suppressible-but-unscored. Z904 is a quality signal, not a security breach.
- **Why:** The old 5-category model (Link Integrity 35%, Orphan Detection 20%, Snippet Validation 20%, Content Quality 15%, Asset Integrity 10%) left Z107, Z505, Z904, Z905 unscored. A 100/100 score that tolerated circular anchors and brand obsolescence was not a true Safe Harbor Guarantee.

### ADR-012: STRICT MODE Transparency (CEO-146)

**[DECISION]** When `--strict` is active, `SentinelReporter.render()` appends a footer line: `STRICT MODE: Warnings have been promoted to errors.`

- **Why:** `--strict` changes the exit code, not what findings are displayed. Without a visible signal, a CI log shows the same output regardless of whether the gate failed due to warnings-as-errors or genuine hard errors. The footer line makes the semantics unambiguous for any engineer reading the log.
- **Invariant:** The footer line is rendered inside the report Panel, after the Sentinel Seal / FAILED verdict, before the info-count summary. It is suppressed in machine formats (`json`, `sarif`) per RULE R20.

### ADR-013: The Suppression Manifesto (CEO-152)

**[DECISION]** Suppression of Z2xx Security findings is architecturally forbidden. `_INVIOLABLE_CODES = frozenset({"Z201", "Z202", "Z203"})` added to `core/rules.py`. `_is_suppressed()` returns `False` immediately for any inviolable code — even if a `zenzic:ignore` comment is present on the same line.

- **Why:** Shield and Blood Sentinel never called `_is_suppressed()` directly, so the gap was safe in practice. But the architectural contract was implicit. Making it explicit guards against future refactors that might accidentally route Z2xx findings through the rule engine.
- **Also:** `BrandObsolescenceRule.check()` gained fence-tracking (`_FENCE_OPEN_RE`) — code block bodies are skipped before Z905 pattern matching. Eliminated false positives in `ecosystem.mdx` (TOML config blocks containing obsolete names in string values).
- **Canonical reference:** `docs/reference/suppression-policy.mdx` (EN+IT) — per-line syntax, inviolable table, `--strict` interaction matrix, Trailing Position Standard (CEO-160).
- **Trailing Position Law (CEO-160):** `zenzic:ignore` comments must appear at the end of the line. In tables: last cell before closing pipe. In prose: absolute end of line. This mirrors `# noqa` / `// eslint-disable-line` convention.

### ADR-014: Quartz Penalty Scorer — Per-Code Deductions with Category Caps (CEO-163/170)

**[DECISION]** `compute_score()` refactored from aggregate decay model to per-code penalty table with category caps.

- **Old model:** `_DECAY_RATE = 0.20` — 5 issues in any category zeroed it regardless of severity (punitive, uniform).
- **New model:** `compute_score(findings_counts: dict[str, int])` with `_CODE_PENALTY` table. Per-code deductions accumulate within each category; the category contribution is clamped to ≥ 0 before weighting.
- **Category Cap Invariant (CEO-175):** 1000 × Z505 (1.0 pt each) hits the Content cap → total = **70/100** (not 0). The cap prevents a single noisy violation type from masking the true structural health signal.
- **Score vs. Gate Separation (CEO-175):** The score is a quality measurement. The `fail_under` threshold is an enforcement policy. They are independent: a score of 70/100 with `fail_under = 80` exits 1. Caps do not weaken the gate.
- **Security override:** Any Z2xx → `score = 0`, `security_override = True`, unconditionally. A leaking credential cannot receive a score.
- **API break:** Old keyword-argument signature (`link_errors=…, orphans=…, …`) removed. `test_scorer.py` fully rewritten.
- **Z501/Z502 split:** `PlaceholderFinding.issue == "short-content"` → Z502 (1.0 pt); else → Z501 (2.0 pt). Reflects severity difference.
- **Ruff-style flat UI (CEO-169):** `SentinelReporter.render()` output is flat — no outer Panel. Bold-cyan `path:line:col` prefix per finding. Security breach Panel preserved.
- **Source-to-Score Integrity (CEO-167):** `LinkError.code` and `SnippetError.code` are computed via `codes.normalize()` in `__post_init__` — findings carry their Zxxx code natively.

### ADR-015: SARIF Sovereign Automation (CEO-221/222)

**[DECISION]** SARIF rule definitions in `cli/_shared.py` are generated dynamically from `codes.py` at runtime.

- **Implementation:** `CODE_DESCRIPTIONS`, `CODE_NAMES`, `CODE_SARIF_LEVELS`, `get_sarif_name()` in `codes.py`. `_shared.py` builds `sarif_rules` via dict comprehension. `helpUri` per rule: `https://zenzic.dev/docs/reference/finding-codes#{code.lower()}`. Ghost codes Z301/Z601/Z701 eliminated. `ZenzicExitCode` class: `SUCCESS=0`, `QUALITY=1`, `SHIELD=2`, `SENTINEL=3`.
- **Why:** Hardcoded SARIF rule lists drifted from `codes.py`. Dynamic generation guarantees perpetual parity — adding a new `Zxxx` code automatically propagates to SARIF output.

### ADR-016: Quartz Auto-Discovery — engine="auto" (CEO-217/218)

**[DECISION]** `engine` field in `ZenzicConfig` defaults to `"auto"`. At runtime, `get_adapter()` resolves `"auto"` via `discover_engine(repo_root)` before cache lookup.

- **Implementation:** `discover_engine()` in `_factory.py`: probes zensical.toml → docusaurus.config.ts/js → mkdocs.yml → `"standalone"`. Z906 NO_FILES_FOUND: note level, exit 0, text-only (RULE R20). `zenzic init`: `_detect_init_engine()` delegates entirely to `discover_engine()`. Generated config sets `fail_under = 100`, `strict = true`.
- **Why:** Old default `"mkdocs"` caused misleading behavior on first run for Docusaurus/Zensical/Standalone projects. `"auto"` makes the out-of-box experience correct without user configuration.

### ADR-017: Sovereign Cartography & Identity Gate (CEO-242/243/244/245/246)

**[DECISION]** `zenzic brain map [PATH]` is the canonical [CODE MAP] update mechanism, replacing the standalone `scripts/map_project.py` for core mapping.

- **Implementation:** `src/zenzic/core/cartography.py` — pure AST scanner (`scan_python_sources`, `render_markdown_table`, `update_ledger`). `src/zenzic/cli/_brain.py` — Typer `brain_app` with `map` command; orchestrates Zone B audit, Trinity Mesh probe, and Master-Shadow Sync (CEO 103-B). `_is_dev_mode()` in `main.py` — PEP 610 `direct_url.json` gate (CEO-246 Identity Gate).
- **Identity Gate (CEO-246):** Detection uses `importlib.metadata.distribution("zenzic").read_text("direct_url.json")` + JSON parse for `dir_info.editable == True`. Zero subprocesses (Pillar 2). Zero filesystem heuristics. Standard PEP 610. False for `pip install zenzic`; True for `pip install -e .`.
- **Dev-mode gating:** When `_is_dev_mode()` is False, `brain_app` is never registered in Typer — the command group is structurally absent, not merely hidden. End-users cannot discover it by guessing.
- **R17 correction (CEO-183 Sovereign Memory Law):** CEO-243 requested "Rule 17 Zero-Amnesia Law". R17 was already occupied (CLI Symmetry CEO-056). The agent surfaced the conflict per CEO-183. The CEO ratified R24 as the correct slot.

<!-- ZONE_B_START -->
## [ACTIVE SPRINT] — Working Context

### D096 — Quartz Discovery, SARIF Sovereignty & Brain Curation (Current)

**Version:** 0.7.0 · **Sprint:** 2026-04-30

**CEO-217 "Quartz Auto-Discovery":** `discover_engine(repo_root) -> str` in `_factory.py`. `engine` default → `"auto"`. Z906 NO_FILES_FOUND (note, exit 0, text-only per R20).

**CEO-221/222 "SARIF Sovereignty":** Dynamic SARIF rules from `codes.py`. `ZenzicExitCode` class. Ghost codes eliminated. `helpUri` per rule at `zenzic.dev`.

**CEO-223 "Shield Invariant Ratified":** `_MAX_LINE_LENGTH` permanently non-configurable. CEO directive blocked by agent; CEO ratified the invariant.

**CEO-224–230 "zenzic init Quartz Template":** `_detect_init_engine()` → `discover_engine()`. Generated `zenzic.toml` sets `fail_under = 100`, `strict = true`.

**CEO-218/219 "Contemporary Testimony":** Z906 in `finding-codes.mdx` EN+IT. Engine `"auto"` in `configuration-reference.mdx` EN+IT. Blog: 20 Acts + Act 19 row.

**CEO-231–237 "Evolutionary Curation":** `CONTRIBUTING.md`: Zenzic Memory Contract. Zone A/B in all 3 public BRAINs. `map_project.py`: Zone B auditor + Trinity Mesh. ADR-015/016.

**CEO-242–246 "Sovereign Cartography & Identity Gate":** `src/zenzic/core/cartography.py` (pure AST scanner). `src/zenzic/cli/_brain.py` (brain sub-app: map, Zone B audit, Trinity Mesh, Master-Shadow Sync). `_is_dev_mode()` in `main.py` (PEP 610 Identity Gate). `just brain-map` wired into `verify`/`preflight`. R24 Zero-Amnesia Law. ADR-017. `tests/test_brain.py` (19 tests). CEO-243 R17 conflict resolved to R24 per Sovereign Memory Law (CEO-183).

**Tests:** 1,371 passed · coverage ≥80% (3.11/3.12/3.13).

### Last Closed — D095 — The Base64 Sentinel Decoder & Universal Path Invariant

**Version:** 0.7.0 · **Sprint:** 2026-04-30

**CEO-194/197/198:** `_BASE64_CANDIDATE_RE` + `_try_decode_base64()` in `shield.py`. B64-encoded PAT → Z201 → Exit 2. KL-001 CLOSED.

**CEO-203 "KL-002 normcase":** `os.path.normcase` in `resolver.py`. 3 new `__slots__`. KL-002 RESOLVED.

**Act 19:** `zenzic lab` 20 total acts (0–19). Fixture `examples/scoring/security-base64/`. Tests: 1,307 passing.

### Last Closed — D094 — Quartz Tribunal Security Audit

Three-team audit (Red/Blue/Purple). BUG-CEO189-01 (CRITICAL) — Z202 exit 1 → exit 3. BUG-CEO189-02..05 — Z106/Z403 label corrections across 7 files. 1,301 tests post-fix. KL-001 + KL-002 documented; both sealed in D095.

<!-- ZONE_B_END -->

## [ARCHIVE LINK]

Complete sprint history, bug post-mortems, and pre-release changelogs:

- **[CHANGELOG.md](CHANGELOG.md)** — current release cycle (v0.7.0)
- **[CHANGELOG.archive.md](CHANGELOG.archive.md)** — pre-v0.6.0 history
