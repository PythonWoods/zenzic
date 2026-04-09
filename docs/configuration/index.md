---
icon: lucide/settings
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Configuration Reference {#configuration-reference}

Zenzic reads a single `zenzic.toml` file at the repository root. All fields are optional — Zenzic works out of the box with no configuration file at all.

!!! tip "Zero configuration"

    Most projects need no `zenzic.toml` at all. Run `uvx --pre zenzic check all` — if it passes,
    you're done. Only add configuration when you need to customise specific behaviour.

---

## Getting started

For most projects, no configuration file is needed. Run `zenzic check all` and Zenzic will locate
the repository root via `.git` or `zenzic.toml` and apply sensible defaults. If no `zenzic.toml`
is found, Zenzic prints a Helpful Hint panel suggesting `zenzic init`.

Use `zenzic init` to scaffold the file automatically. It detects the documentation engine from the
project root (e.g. `mkdocs.yml`) and pre-sets `engine` in `[build_context]`:

```bash
zenzic init             # creates zenzic.toml with detected engine
zenzic init --pyproject # embeds [tool.zenzic] in pyproject.toml instead
zenzic init --force     # overwrite an existing file
```

When `pyproject.toml` exists, `zenzic init` asks whether to embed the configuration there
as a `[tool.zenzic]` table.  Pass `--pyproject` to skip the interactive prompt.

When you need to customise behaviour — for example, to raise the word-count threshold for concise
technical reference pages, or to add team-specific placeholder patterns — create or edit
`zenzic.toml` at the repository root:

```toml
# zenzic.toml — minimal starting point

# Uncomment and adjust the fields you need.
# Everything is optional. Absent fields use their defaults.

# docs_dir = "docs"
# excluded_dirs = ["includes", "assets", "stylesheets", "overrides", "hooks"]
# excluded_assets = []
# snippet_min_lines = 1
# placeholder_max_words = 50
# placeholder_patterns = ["coming soon", "work in progress", "wip", "todo", "stub", ...]

# [build_context]           # required only for folder-mode multi-locale projects
# engine         = "mkdocs" # "mkdocs" or "zensical"
# default_locale = "en"
# locales        = ["it"]   # non-default locale directory names
```

---

## Reference sections

This reference is split into focused pages:

| Page | Contents |
| :--- | :--- |
| [Core Settings](core-settings.md) | `docs_dir`, exclusion lists, thresholds, scoring, loading behaviour |
| [Adapters & Engine](adapters-config.md) | `build_context`, adapter auto-detection, `--engine` override |
| [Custom Rules DSL](custom-rules-dsl.md) | `[[custom_rules]]` — project-specific regex lint rules in pure TOML |

---

## Full example

The simplest complete `zenzic.toml` that exercises every section:

```toml
docs_dir = "docs"
excluded_dirs  = ["includes", "assets", "stylesheets", "overrides", "hooks"]
excluded_assets = []
excluded_build_artifacts = []
snippet_min_lines = 1
placeholder_max_words = 50
placeholder_patterns = ["coming soon", "work in progress", "wip", "todo", "stub", "draft", "tbd", "da completare", "bozza"]
validate_same_page_anchors = false
excluded_external_urls = []
fail_under = 80

[[custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Remove DRAFT marker before publishing."
severity = "warning"

[build_context]
engine         = "mkdocs"
default_locale = "en"
locales        = ["it"]
```

---

## Configuration loading

Zenzic follows a three-level **Agnostic Citizen** priority chain when searching for configuration
at startup:

| Priority | Source | When used |
| :---: | :--- | :--- |
| 1 | `zenzic.toml` at repository root | Always preferred — the authoritative sovereign config |
| 2 | `[tool.zenzic]` in `pyproject.toml` | Used only when `zenzic.toml` is absent |
| 3 | Built-in defaults | Used when neither file is present |

The repository root is located by walking upward from the current working directory until a `.git`
directory, a `zenzic.toml`, or a `pyproject.toml` is found.

### zenzic.toml (Priority 1)

The dedicated configuration file. If it exists, Zenzic reads it and ignores `pyproject.toml`
entirely — there is no merging between the two files.

### pyproject.toml (Priority 2) — v0.5.0a1

Python projects that already have a `pyproject.toml` can embed Zenzic configuration in the
`[tool.zenzic]` table, eliminating the need for a separate file:

```toml
# pyproject.toml — embed Zenzic config in the standard Python metadata file

[tool.zenzic]
docs_dir   = "docs"
fail_under = 90

[tool.zenzic.build_context]
engine = "mkdocs"

[[tool.zenzic.custom_rules]]
id       = "ZZ-NODRAFT"
pattern  = "(?i)\\bDRAFT\\b"
message  = "Remove DRAFT marker before publishing."
severity = "warning"
```

All fields supported in `zenzic.toml` are equally supported in `[tool.zenzic]`. The
`[build_context]` sub-table becomes `[tool.zenzic.build_context]`, and `[[custom_rules]]` arrays
become `[[tool.zenzic.custom_rules]]`.

!!! note "Sovereignty rule"
    If both `zenzic.toml` **and** `pyproject.toml` exist in the repository root, `zenzic.toml`
    wins unconditionally. The `[tool.zenzic]` table in `pyproject.toml` is ignored.

### Error handling

If the winning config file contains a **TOML syntax error**, Zenzic raises a `ConfigurationError`
with a human-friendly message and exits immediately — silent fallback on a broken config file
would hide mistakes. Unknown fields are silently ignored, which means adding fields not yet
supported by your installed version is safe.
