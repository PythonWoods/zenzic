<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# 💎 Zenzic v0.7.0 — The Quartz Era (Quartz Maturity)

This release marks the birth of the Sovereign Knowledge System. Following the Quartz Purgation, Zenzic definitively abandons all experimental residues to become a deterministic, industrial-grade infrastructure.

## 🏛️ The Pillars of v0.7.0

- **Deterministic Integrity**: Complete absence of any probabilistic dependency or logic. Zenzic now operates exclusively on structural facts and certain invariants.
- **Sentinel Seal**: A 4-stage validation system (4-Gates Standard) ensuring absolute quality before every push.
- **Cross-Repo Governance**: Implementation of the Branch Parity Rule for perfect synchronization between code and documentation.
- **Machine Silence**: Optimization of analysis flows for native CI/CD integration via the SARIF 2.1.0 standard.

## ⚠️ Evolution Note (Breaking Changes)

v0.7.0 is Year Zero. Previous versions are officially deprecated as they do not follow the current Diátaxis architecture. Every reference to old brands or legacy architectures has been removed to make way for a lean ecosystem focused on source purity.

## 🚀 Towards the Future

With this release, Zenzic is no longer just a tool, but a trust platform for documentation engineering.

---
**PythonWoods** <dev@pythonwoods.dev>
*Target Release Date: 2026-05-XX*

---

## ⚠️ Breaking Changes

| Change | Migration |
| :--- | :--- |
| MkDocs plugin (`zenzic.integrations.mkdocs`) removed | Remove `plugins: - zenzic` from `mkdocs.yml`; add `zenzic check all` as a CI step |
| `engine = "vanilla"` removed | Replace with `engine = "standalone"` in `zenzic.toml` |
| `zenzic plugins` command removed | Use `zenzic inspect capabilities` |
| `just preflight` recipe removed; pipeline collapsed into `just verify` | Run `uvx pre-commit install -t pre-push` after `just sync` to install the new Final Guard |
| `nox -s preflight` session removed (duplicated `just verify`) | Run `just verify` locally; CI invokes the same command |
| `just test` no longer produces coverage by default (now `pytest -n auto`) | Use `just test-cov` for the audit run with `coverage.xml` |

---

## 🛡️ EPOCH 4 — The Safe Port (4-Gates Standard)

v0.7.0 introduces the **atomic single entry-point** for quality:

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

v0.7.0 closes the last gap in the documentation integrity story:
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
v0.7.0 introduces a **declarative trust contract**:

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

**Known limitations:** The ReDoS canary (`_CANARY_STRINGS` / `_assert_regex_canary`) uses
`SIGALRM` and is a **no-op on Windows** — the 50 ms interrupt is not available on that
platform. Plugin authors on Windows operate without startup ReDoS validation in v0.7.0.
Deterministic enforcement via a process-based watchdog is planned for v0.8.0 "Basalt".

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
