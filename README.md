<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# 🛡️ Zenzic

<p align="center">
  <img src="docs/assets/brand/svg/zenzic-wordmark.svg#gh-light-mode-only" alt="Zenzic" width="360">
  <img src="docs/assets/brand/svg/zenzic-wordmark-dark.svg#gh-dark-mode-only" alt="Zenzic" width="360">
</p>

<p align="center">
  <a href="https://pypi.org/project/zenzic/"><img src="https://img.shields.io/pypi/v/zenzic?include_prereleases&color=38bdf8&style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/zenzic/"><img src="https://img.shields.io/pypi/pyversions/zenzic?color=10b981&style=flat-square" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-0d9488?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/PythonWoods/zenzic"><img src="https://img.shields.io/badge/🛡️_zenzic_shield-passing-4f46e5?style=flat" alt="Zenzic Shield"></a>
  <a href="https://github.com/PythonWoods/zenzic"><img src="https://img.shields.io/badge/🛡️_zenzic-100%2F100-4f46e5?style=flat" alt="Zenzic Score"></a>
  <a href="https://zensical.org/"><img src="https://img.shields.io/badge/docs_by-Zensical-000000?style=flat" alt="Powered by Zensical"></a>
</p>

<p align="center">
  <strong>"Zenzic is the silent guardian of your documentation. It doesn't just check links; it audits your brand's technical integrity."</strong><br>
  <em>Engineering-grade documentation linter — standalone, engine-agnostic, and security-hardened.</em>
</p>

---

> Documentation doesn't fail loudly. It decays silently.

Broken links, orphan pages, invalid code snippets, stale placeholder content, and leaked API keys
accumulate over time — until users hit them in production. Zenzic catches all of these across
[MkDocs][mkdocs] and [Zensical][zensical] projects as a **standalone CLI**.

Zenzic is **agnostic** — it works with any Markdown-based documentation system (MkDocs, Zensical,
or a bare folder of `.md` files) without installing any build framework. And it is **opinionated**:
absolute links are a hard error, and if you declare `engine = "zensical"` you must have
`zensical.toml` — no fallback, no guessing.

---

## v0.5.0a1 Highlights — The Sentinel

- **Hybrid Adaptive Engine**: `scan_docs_references` is the single unified
  entry point for all scan modes. The engine selects sequential or parallel
  execution automatically based on repository size (threshold: 50 files). No
  flags required — Zenzic is fast by default.
- **`AdaptiveRuleEngine` with eager pickle validation**: all rules are validated
  for pickle-serializability at construction time. A non-serialisable rule raises
  `PluginContractError` immediately — before any file is scanned.
- **`zenzic.rules` entry-point group**: core rules (`VSMBrokenLinkRule`) are
  registered as first-class plugins. Third-party packages can extend Zenzic by
  registering under the same group and enabling their plugin ID in `zenzic.toml`.
- **`zenzic plugins list`**: new command that displays every rule registered in
  the `zenzic.rules` entry-point group — Core rules and third-party plugins.
- **`pyproject.toml` support (ISSUE #5)**: embed Zenzic config in `[tool.zenzic]`
  when `zenzic.toml` is absent. `zenzic.toml` always wins if both exist.
- **Performance telemetry**: `scan_docs_references(verbose=True)` prints engine
  mode, worker count, elapsed time, and estimated speedup to stderr.
- **`PluginContractError`**: new exception for rule contract violations.
- **Plugin documentation**: `docs/developers/plugins.md` (EN + IT) — full
  contract, packaging instructions, and `pyproject.toml` registration examples.
- **Release-track clarification**: the 0.4.x cycle is considered abandoned
  (exploratory with repeated breaking changes); 0.5.x is the active
  stabilization line.

---

## 📖 Documentation

Zenzic provides an extensive, engineering-grade documentation portal:

- 🚀 **[User Guide][docs-home]**: Installation, CLI usage, and all available checks.
- 🏅 **[Badges][docs-badges]**: Official Zenzic Shield and Score badge snippets for your README.
- 🔄 **[CI/CD Integration][docs-cicd]**: GitHub Actions workflows, dynamic badges, and regression detection.
- ⚙️ **[Developer Guide][docs-arch]**: Deep dive into the deterministic pure-core architecture, Two-Pass Pipeline, and state-machine parsing.
- 🤝 **[Contributing][docs-contributing]**: Set up the local development environment (`uv`, `nox`), run the test suite, and submit PRs.

<p align="center">
  <a href="https://zenzic.pythonwoods.dev/"><strong>Explore the full documentation →</strong></a>
</p>

---

![Zenzic CLI Output][screenshot]

---

## What Zenzic checks

| Check | CLI command | What it detects |
| --- | --- | --- |
| Links | `zenzic check links` | Broken internal links, dead anchors, and **path traversal** attempts |
| Orphans | `zenzic check orphans` | `.md` files absent from `nav` |
| Snippets | `zenzic check snippets` | Python, YAML, JSON, and TOML blocks with syntax errors |
| Placeholders | `zenzic check placeholders` | Stub pages and forbidden text patterns |
| Assets | `zenzic check assets` | Images and files not referenced anywhere |
| **References** | `zenzic check references` | Dangling References, Dead Definitions, **Zenzic Shield** |

Beyond pass/fail, `zenzic score` aggregates all checks into a deterministic 0–100 quality score.
`zenzic diff` compares the current score against a saved baseline — enabling regression detection
on every pull request.

**Autofix:** Zenzic also provides active cleanup utilities. Run `zenzic clean assets` to automatically deleting the unused images identified by `check assets` (interactive or via `-y`).

---

## Portability Standards

Zenzic enforces two rules that make documentation portable across any hosting environment
and independent of any specific build engine.

### Relative Path Enforcement

Zenzic **rejects internal links that start with `/`**. Absolute paths are environment-dependent:
a link to `/assets/logo.png` works when the site is at the domain root, but returns 404 when
hosted in a subdirectory (e.g. `https://example.com/docs/assets/logo.png` ≠
`https://example.com/assets/logo.png`).

```markdown
<!-- Rejected by Zenzic -->
[Download](/assets/guide.pdf)

<!-- Correct — works at any hosting path -->
[Download](../assets/guide.pdf)
```

The error message includes an explicit fix suggestion. External URLs (`https://...`) are not
affected.

### i18n Support: Suffix Mode and Folder Mode

Zenzic natively supports both i18n strategies used by `mkdocs-static-i18n`:

**Suffix Mode** (`page.locale.md`) — translated files are siblings of the originals:

```text
docs/
  guide.md        ← default locale (EN)
  guide.it.md     ← Italian translation (same depth, path-symmetric)
  assets/
    logo.png      ← shared asset, same relative path from both files
```

**Folder Mode** (`docs/it/page.md`) — non-default locales live in a top-level directory:

```text
docs/
  guide.md
  assets/
    logo.png
  it/
    guide.md      ← Italian translation
```

In Folder Mode, Zenzic uses the `[build_context]` section in `zenzic.toml` to know which
top-level directories are locale trees. Asset links from `docs/it/guide.md` that resolve to
`docs/it/assets/logo.png` are automatically re-checked against `docs/assets/logo.png` —
mirroring the engine's own fallback behaviour. Locale files are never reported as orphans.

```toml
# zenzic.toml
[build_context]
engine         = "mkdocs"      # "mkdocs" or "zensical"
default_locale = "en"
locales        = ["it", "fr"]  # non-default locale directory names
```

When `zenzic.toml` is absent, Zenzic reads locale configuration directly from `mkdocs.yml`
(respecting `docs_structure`, `fallback_to_default`, and `languages`). No configuration is
required for projects that do not use i18n.

## First-Class Integrations

Zenzic is **build-engine agnostic**. It works with any Markdown-based documentation system —
MkDocs, Zensical, or a bare folder of `.md` files. No build framework needs to be installed;
Zenzic reads raw source files only.

Where a documentation ecosystem defines well-known conventions for multi-locale structure or
build-time artifact generation, Zenzic provides enhanced, opt-in support by reading the project's
configuration file as plain YAML — never by importing or executing the framework itself.

### Engine Adapters

Zenzic translates engine-specific knowledge into engine-agnostic answers through a thin
**adapter layer**:

```text
zenzic.toml  →  get_adapter()  →  Adapter  →  Core (Scanner + Validator)
```

The adapter answers the questions the Core needs without knowing anything about MkDocs or
Zensical internals:

| Method | Question |
| :--- | :--- |
| `is_locale_dir(part)` | Is this path component a non-default locale directory? |
| `resolve_asset(path)` | Does a default-locale fallback exist for this missing asset? |
| `is_shadow_of_nav_page(rel, nav)` | Is this locale file a mirror of a nav-listed page? |
| `get_nav_paths()` | Which `.md` paths are declared in the nav? |
| `get_ignored_patterns()` | Which filename patterns are non-default locale files (suffix mode)? |

Three adapters are available, selected automatically by `get_adapter()`:

| Adapter | When selected | Config source |
| :--- | :--- | :--- |
| `MkDocsAdapter` | `engine = "mkdocs"` or unknown engine | `mkdocs.yml` (YAML) |
| `ZensicalAdapter` | `engine = "zensical"` | `zensical.toml` (TOML, zero YAML) |
| `VanillaAdapter` | No config file, no locales declared | — (all no-ops) |

**Native Enforcement** — `engine = "zensical"` requires `zensical.toml` to be present.
If it is absent, Zenzic raises `ConfigurationError` immediately. There is no fallback to
`mkdocs.yml` and no silent degradation. Zensical identity must be provable.

### How it works — Virtual Site Map (VSM)

Most documentation linters check whether a linked file exists on disk.
Zenzic goes further: it builds a **Virtual Site Map** before any rule fires.

```text
Source files  ──►  Adapter  ──►  VSM  ──►  Rule Engine  ──►  Violations
  .md + config      (engine-       (URL → status)   (pure functions)
                    specific
                    knowledge)
```

The VSM maps every `.md` source file to the canonical URL the build engine
will serve — **without running the build**. Each route carries a status:

| Status | Meaning |
| :--- | :--- |
| `REACHABLE` | Page is in the nav; users can find it. |
| `ORPHAN_BUT_EXISTING` | File exists on disk but is absent from `nav:`. Users cannot find it via navigation. |
| `CONFLICT` | Two files map to the same URL (e.g. `index.md` + `README.md`). Build result is undefined. |
| `IGNORED` | File will not be served (unlisted `README.md`, Zensical `_private/` dirs). |

This makes Zenzic uniquely precise: a link to an `ORPHAN_BUT_EXISTING` page
is caught as `UNREACHABLE_LINK` — the file exists, the link resolves, but
the user will hit a 404 after the build because the page is not navigable.

**Ghost Routes** (`reconfigure_material: true`) — when `mkdocs-material`
auto-generates locale entry points (e.g. `/it/`) at build time, those pages
never appear in `nav:`. Zenzic detects this flag and marks them `REACHABLE`
automatically, so no false orphan warnings are emitted.

**Content-addressable cache** — Zenzic avoids re-linting unchanged files by
keying results on `SHA256(content) + SHA256(config)`. For VSM-aware rules
the key also includes `SHA256(vsm_snapshot)`, ensuring invalidation when any
file's routing state changes. Timestamps are never consulted — the cache is
correct in CI environments where `git clone` resets `mtime`.

### MkDocs — i18n fallback

When `mkdocs.yml` declares the i18n plugin with `fallback_to_default: true`, Zenzic mirrors
the plugin's resolution logic: a link from a translated page to an untranslated page is **not**
reported as broken, because the build will serve the default-locale version. Supported for both
`docs_structure: suffix` and `docs_structure: folder`.

```yaml
# mkdocs.yml
plugins:
  - i18n:
      docs_structure: folder
      fallback_to_default: true
      languages:
        - locale: en
          default: true
          build: true
        - locale: it
          build: true
```

If `mkdocs.yml` is absent (or the i18n plugin is not configured), Zenzic falls back to standard
single-locale validation — no errors, no warnings, no framework required.

### Build-time artifacts (`excluded_build_artifacts`)

Applies to any documentation system. If links point to files generated at build time (PDFs,
ZIPs), declare their glob patterns in `zenzic.toml`:

```toml
# zenzic.toml
excluded_build_artifacts = ["pdf/*.pdf", "dist/*.zip"]
```

Zenzic suppresses errors for matching paths at lint time. The build remains responsible for
generating the artifacts; Zenzic trusts the link without requiring the file on disk.

### Reference-style links

`[text][id]` links are resolved through the same pipeline as inline links — including i18n
fallback — for all documentation systems.

```markdown
[API Reference][api-ref]

[api-ref]: api.md
```

---

## Installation

### With `uv` (recommended)

[`uv`][uv] is the fastest way to install and run Zenzic:

```bash
# Zero-install, one-shot audit
uvx zenzic check all

# Global CLI tool — available in any project
uv tool install zenzic

# Project dev dependency — version-pinned in uv.lock
uv add --dev zenzic
```

### With `pip`

```bash
# Global install (consider a virtual environment)
pip install zenzic

# Inside a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install zenzic
```

### MkDocs rendering — `zenzic[docs]` extra

Zenzic's core is dependency-free: linting raw Markdown requires nothing beyond `zenzic`.
The MkDocs stack is only needed to **render** your site, not to validate it.

If you use MkDocs and also want the full build stack available:

```bash
# uv
uv add --dev "zenzic[docs]"

# pip
pip install "zenzic[docs]"
```

> **Note:**
> All seven checks — including `check links --strict` and `check references` — work on raw Markdown
> source files via a native Python parser and `httpx`. **No MkDocs or Zensical installation is required**
> for `check`, `score`, or `diff`.
>
> **Build artifacts:** If your documentation links to files generated at build time
> (PDFs, ZIPs), add their glob patterns to `excluded_build_artifacts` in `zenzic.toml`
> rather than pre-generating them. See the [First-Class Integrations](#first-class-integrations) section above.

---

## CLI usage

```bash
# Individual checks
zenzic check links --strict
zenzic check orphans
zenzic check snippets
zenzic check placeholders
zenzic check assets

# Autofix & Cleanup
zenzic clean assets               # Interactively delete unused assets
zenzic clean assets -y            # Delete unused assets immediately
zenzic clean assets --dry-run     # Preview what would be deleted

# Reference pipeline (v0.2.0)
zenzic check references           # Harvest → Cross-Check → Shield → Integrity score
zenzic check references --strict  # Treat Dead Definitions as errors
zenzic check references --links   # Also validate reference URLs via async HTTP

# All checks in one command
zenzic check all --strict
zenzic check all --exit-zero      # Report without blocking the pipeline
zenzic check all --format json    # Machine-readable output

# Quality score (0–100)
zenzic score
zenzic score --save               # Persist baseline snapshot
zenzic score --fail-under 80      # Exit 1 if below threshold

# Regression detection against saved snapshot
zenzic diff                       # Exit 1 on any score drop
zenzic diff --threshold 5         # Exit 1 only if drop > 5 points

# Development server (engine-agnostic)
zenzic serve                      # Auto-detect mkdocs or zensical
zenzic serve --engine mkdocs
zenzic serve --port 9000
zenzic serve --no-preflight
```

### Exit codes

| Code | Meaning |
| :---: | :--- |
| `0` | All selected checks passed |
| `1` | One or more checks reported issues |
| **`2`** | **SECURITY CRITICAL — Zenzic Shield detected a leaked credential** |

> **Warning:**
> **Exit code 2** is reserved exclusively for security events. If `zenzic check references` exits
> with code 2, a secret (OpenAI API key, GitHub token, or AWS access key) was found embedded in a
> reference URL inside your documentation. Rotate the credential immediately.

---

## 🛡️ Zenzic Shield

The **Zenzic Shield** is a two-layer security system built into the core engine:

| Layer | Introduced | Protects against |
| --- | --- | --- |
| **Credential detection** | v0.2.0 | Leaked API keys / tokens embedded in reference URLs |
| **Path traversal** | v0.3.0 | `../../../../etc/passwd`-style escape from `docs/` |

### Credential detection

The credential layer runs during **Pass 1** (Harvesting) of the reference pipeline and scans
every reference URL for known credential patterns before any HTTP request is issued.

```markdown
<!-- This definition would trigger an immediate Exit 2 -->
[api-docs]: https://api.example.com/?key=sk-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789012345678901
```

```text
╔══════════════════════════════════════╗
║        SECURITY CRITICAL             ║
║  Secret(s) detected in documentation ║
╚══════════════════════════════════════╝

  [SHIELD] docs/api.md:12 — openai-api-key detected in URL
    https://api.example.com/?key=sk-AbCdEfGhIj...

Build aborted. Rotate the exposed credential immediately.
```

**How it works:**

1. The Shield runs *inside* Pass 1 — before Pass 2 validates links and before any HTTP ping is
   issued. A document containing a leaked credential is never used to make outbound requests.
2. Patterns use exact-length quantifiers (`{48}`, `{36}`, `{16}`) — no backtracking, O(1) per line.
3. Seven credential families are covered out of the box:

| Type | Pattern |
| --- | --- |
| OpenAI API key | `sk-[a-zA-Z0-9]{48}` |
| GitHub token | `gh[pousr]_[a-zA-Z0-9]{36}` |
| AWS access key | `AKIA[0-9A-Z]{16}` |
| Stripe live key | `sk_live_[0-9a-zA-Z]{24}` |
| Slack token | `xox[baprs]-[0-9a-zA-Z]{10,48}` |
| Google API key | `AIza[0-9A-Za-z\-_]{35}` |
| PEM private key | `-----BEGIN [A-Z ]+ PRIVATE KEY-----` |

1. **No blind spots** — the Shield scans every line of the source file, including lines inside
   fenced code blocks (`bash`, `yaml`, unlabelled, etc.). A credential committed inside a code
   example is still a committed credential.

> **Tip:**
> Add `zenzic check references` to your pre-commit hooks to catch leaked credentials before they
> are ever committed to version control.

### Path traversal (v0.3.0)

The path traversal layer runs inside `InMemoryPathResolver` during `check links`. It normalises
every resolved href with `os.path.normpath` (pure C, zero kernel calls) and verifies the result
is contained within `docs/` using a single string prefix check — $O(1)$, allocation-free.

```text
Attack href:   ../../../../etc/passwd
After resolve: /etc/passwd
Shield check:  /etc/passwd does not start with /docs/ → PathTraversal returned, link rejected
```

Any href that escapes the docs root is surfaced as a distinct `PathTraversal` error — never
silently collapsed into a generic "file not found".

---

## CI/CD integration

### GitHub Actions

```yaml
- name: Lint documentation
  run: uvx zenzic check all

- name: Check references and run Shield
  run: uvx zenzic check references
```

Full workflow: [`.github/workflows/zenzic.yml`][ci-workflow]

For dynamic badge automation and regression detection, see the [CI/CD Integration guide][docs-cicd].

---

## Configuration

All fields are optional. Zenzic works with no configuration file at all.

Zenzic follows a three-level **Agnostic Citizen** priority chain:

1. `zenzic.toml` at the repository root — sovereign; always wins.
2. `[tool.zenzic]` in `pyproject.toml` — used when `zenzic.toml` is absent.
3. Built-in defaults.

```toml
# zenzic.toml  (or [tool.zenzic] in pyproject.toml)
docs_dir = "docs"
excluded_dirs = ["includes", "assets", "stylesheets", "overrides", "hooks"]
snippet_min_lines = 1
placeholder_max_words = 50
placeholder_patterns = ["coming soon", "todo", "stub"]
fail_under = 80   # exit 1 if score drops below this; 0 = observational mode

# Engine and i18n context — required only for folder-mode multi-locale projects.
# When absent, Zenzic reads locale config directly from mkdocs.yml.
[build_context]
engine         = "mkdocs"   # "mkdocs" or "zensical"
default_locale = "en"
locales        = ["it"]     # non-default locale directory names
```

---

## Development

For a faster, interactive development workflow using **just**, or for detailed instructions on
adding new checks, see the [Contributing Guide][contributing].

```bash
uv sync --group dev
nox -s dev         # Install pre-commit hooks (once)

nox -s tests       # pytest + coverage
nox -s lint        # ruff check
nox -s format      # ruff format
nox -s typecheck   # mypy --strict
nox -s docs        # mkdocs build --strict
nox -s preflight   # zenzic check all (self-check)
```

---

## Contributing

We welcome bug reports, documentation improvements, and pull requests. Before you start:

1. Open an issue to discuss the change — use the [bug report][issues], [feature request][issues], or [docs issue][issues] template.
2. Read the [Contributing Guide][contributing] — especially the **Local development setup** and the **Zenzic Way** checklist (pure functions, no subprocesses, source-first).
3. Every PR must pass `nox -s preflight` (tests + lint + typecheck + self-dogfood) and include REUSE/SPDX headers on new files.

Please also review our [Code of Conduct][coc] and [Security Policy][security].

## Citing Zenzic

A [`CITATION.cff`][citation-cff] file is present at the root of the repository. GitHub renders
it automatically — click **"Cite this repository"** on the repo page for APA or BibTeX output.

## License

Apache-2.0 — see [LICENSE][license].

---

<p align="center">
  &copy; 2026 <strong>PythonWoods</strong>. Engineered with precision.<br>
  Based in Italy 🇮🇹 &nbsp;·&nbsp; Committed to the craft of Python development.<br>
  <a href="mailto:dev@pythonwoods.dev">dev@pythonwoods.dev</a>
</p>

<!-- ─── Reference link definitions ──────────────────────────────────────────── -->

[mkdocs]:            https://www.mkdocs.org/
[zensical]:          https://zensical.org/
[uv]:                https://docs.astral.sh/uv/
[docs-home]:         https://zenzic.pythonwoods.dev/
[docs-badges]:       https://zenzic.pythonwoods.dev/usage/badges/
[docs-cicd]:         https://zenzic.pythonwoods.dev/ci-cd/
[docs-arch]:         https://zenzic.pythonwoods.dev/architecture/
[docs-contributing]: https://zenzic.pythonwoods.dev/community/contribute/
[screenshot]:        docs/assets/screenshots/screenshot.svg
[ci-workflow]:       .github/workflows/zenzic.yml
[contributing]:      CONTRIBUTING.md
[license]:           LICENSE
[citation-cff]:      CITATION.cff
[coc]:               CODE_OF_CONDUCT.md
[security]:          SECURITY.md
[issues]:            https://github.com/PythonWoods/zenzic/issues
