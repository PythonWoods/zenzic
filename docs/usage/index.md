---
icon: lucide/play
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Getting Started

Zenzic reads directly from the filesystem and works with any Markdown-based project. Use it
in local development, as a pre-commit hook, in CI pipelines, or for one-off audits.

## Canonical examples

The repository ships maintained fixtures that mirror the documented contracts:

- `examples/mkdocs-basic/` — MkDocs 1.6 baseline (nested nav, external nav link,
  tolerant YAML tags like `!ENV` and `!relative`).
- `examples/i18n-standard/` — strict bilingual gold standard.
- `examples/zensical-basic/` — Zensical v0.0.31+ baseline (`[project].nav`).
- `examples/broken-docs/` — intentional failures (exit 1).
- `examples/security_lab/` — security fixture (Shield exit 2).

!!! tip "Just want to run it now?"

    ```bash
    uvx zenzic check all
    ```

    No installation required. `uvx` downloads and runs Zenzic in a throwaway environment.

---

## Install

### Ephemeral — no installation required

=== ":simple-astral: uv"

    ```bash
    uvx zenzic check all
    ```

    `uvx` resolves and runs Zenzic from PyPI in a throwaway environment. Nothing is installed on
    your system. The right choice for one-off audits, `git hooks`, and CI jobs where you want to
    avoid pinning a dev dependency.

=== ":simple-pypi: pip"

    ```bash
    pip install zenzic
    zenzic check all
    ```

    Standard installation into the active environment. Use inside a virtual environment to keep
    your system Python clean.

### Global tool — available in every project

=== ":simple-astral: uv"

    ```bash
    uv tool install zenzic
    zenzic check all
    ```

    Install once, use in any project. The binary is available on your `PATH` without activating
    a virtual environment.

=== ":simple-pypi: pip"

    ```bash
    python -m venv ~/.local/zenzic-env
    source ~/.local/zenzic-env/bin/activate   # Windows: .venv\Scripts\activate
    pip install zenzic
    ```

    Install into a dedicated virtual environment, then add the `bin/` directory to your `PATH`.

### Project dev dependency — version pinned per project

=== ":simple-astral: uv"

    ```bash
    uv add --dev zenzic
    uv run zenzic check all
    ```

    Installs Zenzic into the project's virtual environment and pins the version in `uv.lock`.
    The right choice for team projects where everyone must use the same version, and for CI
    pipelines that install project dependencies before running checks.

=== ":simple-pypi: pip"

    ```bash
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install zenzic
    zenzic check all
    ```

    Standard dev-dependency pattern with a project-local virtual environment.

### The `zenzic[docs]` extra — for rendering, not linting

Zenzic reads `mkdocs.yml` as plain YAML using its own `_PermissiveYamlLoader` (a
`yaml.SafeLoader` subclass that silently ignores engine-specific tags like `!ENV`). It
**does not import `mkdocs`, `mkdocs-material`, or any plugin package** to parse your
configuration. PyYAML is a core dependency — no extra required.

The `[docs]` extra (`mkdocs-material`, `mkdocstrings`, `mkdocs-minify-plugin`,
`mkdocs-static-i18n`) is the build stack used to **render Zenzic's own documentation
site**. It is a contributor dependency, not a user dependency:

- **Linting your MkDocs project:** install `zenzic` only.
- **Building Zenzic's documentation site locally:** install `zenzic[docs]`.

```bash
# Lint any MkDocs project — no extras needed
uvx zenzic check all

# Build Zenzic's own docs site (contributor workflow only)
uv add --dev "zenzic[docs]"
mkdocs serve
```

!!! note "Third-party engine adapters"
    Third-party adapters (e.g. a hypothetical `zenzic-hugo-adapter`) are separate
    installable packages — not extras of `zenzic` itself. No extra is required for
    `VanillaAdapter` (plain Markdown folders).

---

## Init → Config → Check workflow

The standard workflow for adopting Zenzic in a project:

### 1. Init — scaffold a configuration file

Bootstrap a `zenzic.toml` with a single command. Zenzic auto-detects the documentation engine and
pre-populates `[build_context]` accordingly:

```bash
zenzic init
```

**Example output when `mkdocs.yml` is present:**

```text
Created zenzic.toml
  Engine pre-set to mkdocs (detected from mkdocs.yml).

Edit the file to enable rules, adjust directories, or set a quality threshold.
Run zenzic check all to validate your documentation.
```

If no engine config file is found, `zenzic init` produces an engine-agnostic scaffold (Vanilla
mode). In either case, all settings are commented out by default — uncomment and adjust only the
fields you need.

Run Zenzic without a `zenzic.toml` and it falls back to built-in defaults, printing a Helpful
Hint panel that suggests `zenzic init`:

```text
╭─ 💡 Zenzic Tip ─────────────────────────────────────────────────────╮
│ Using built-in defaults — no zenzic.toml found.                      │
│ Run zenzic init to create a project configuration file.              │
│ Customise docs directory, excluded paths, engine adapter, and rules. │
╰──────────────────────────────────────────────────────────────────────╯
```

### 2. Config — tune to your project

Edit the generated `zenzic.toml` to suppress noise and set thresholds appropriate to your project:

```toml
# zenzic.toml — place at the repository root
excluded_assets = [
    "assets/favicon.svg",      # referenced by mkdocs.yml, not by any .md page
    "assets/social-preview.png",
]
placeholder_max_words = 30     # technical reference pages are intentionally brief
fail_under = 70                # establish an initial quality floor
```

See the [Configuration Reference](../configuration/index.md) for the full field list.

### 3. Check — run continuously

With the baseline established, run Zenzic on every commit and pull request:

```bash
# Pre-commit hook or CI step
# --strict: validate external URLs + treat warnings as errors
zenzic check all --strict

# Save a quality baseline on main
zenzic score --save

# Block PRs that regress the baseline by more than 5 points
zenzic diff --threshold 5
```

---

## Engine modes

Zenzic operates in one of two modes depending on whether it can discover a build-engine
configuration file:

### Engine-aware mode

When `mkdocs.yml` (MkDocs/Zensical) or `zensical.toml` (Zensical) is present at the repository
root, Zenzic loads the corresponding **adapter** which provides:

- **Nav awareness** — orphan detection knows the difference between "not in the nav" and "not
  supposed to be in the nav" (e.g. i18n locale files).
- **i18n fallback** — cross-locale links are resolved correctly instead of being flagged as broken.
- **Locale directory suppression** — files under `docs/it/`, `docs/fr/`, etc. are not reported
  as orphans.
- **Ghost Routes** — when `mkdocs-material` with `reconfigure_material: true` generates locale
  entry points (e.g. `/it/`) at build time, those pages never appear in `nav:`. Zenzic
  marks them `REACHABLE` automatically in the [Virtual Site Map](../architecture.md#virtual-site-map-vsm)
  so they are never reported as false orphans — with no manual exclusion list required.

### Vanilla mode

When no build-engine configuration is found, Zenzic falls back to `VanillaAdapter`. In this mode:

- **Orphan check is skipped.** Without a nav declaration, every file would appear to be an orphan.
- **All other checks run normally** — links, snippets, placeholders, assets, and references.

Vanilla mode is the right choice for plain Markdown wikis, GitHub-wiki repos, or any project
where navigation is implicit rather than declared.

!!! tip "Force a specific mode"
    Use `--engine` to override the detected adapter for a single run:

    ```bash
    zenzic check all --engine vanilla    # skip orphan check regardless of config files
    zenzic check all --engine mkdocs     # force MkDocs adapter
    ```

---

**Next steps:**

- [CLI Commands reference](commands.md) — every command, flag, and exit code
- [Advanced features](advanced.md) — Reference integrity, Shield, programmatic usage
- [CI/CD Integration](../ci-cd.md) — GitHub Actions, pre-commit hooks, baseline management
