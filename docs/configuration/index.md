---
icon: lucide/settings
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Configuration Reference

Zenzic reads a single `zenzic.toml` file at the repository root. All fields are optional — Zenzic works out of the box with no configuration file at all.

!!! tip "Zero configuration"

    Most projects need no `zenzic.toml` at all. Run `uvx zenzic check all` — if it passes,
    you're done. Only add configuration when you need to customise specific behaviour.

---

## Getting started

For most projects, no configuration file is needed. Run `zenzic check all` and Zenzic will locate
the repository root via `.git` or `zenzic.toml` and apply sensible defaults. If no `zenzic.toml`
is found, Zenzic prints a Helpful Hint panel suggesting `zenzic init`.

Use `zenzic init` to scaffold the file automatically. It detects the documentation engine from the
project root (e.g. `mkdocs.yml`) and pre-sets `engine` in `[build_context]`:

```bash
zenzic init          # creates zenzic.toml with detected engine
zenzic init --force  # overwrite an existing file
```

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

Zenzic reads `zenzic.toml` from the repository root at startup. The repository root is located by
walking upward from the current working directory until a `.git` directory or a `zenzic.toml`
file is found.

If `zenzic.toml` is absent, all defaults apply silently. If `zenzic.toml` is present but contains
a **TOML syntax error**, Zenzic raises a `ConfigurationError` with a human-friendly message and
exits immediately — silent fallback on a broken config file would hide mistakes. Unknown fields
are silently ignored, which means adding fields not yet supported by your installed version is
safe.
