---
sidebar_label: Overview
description: "Checks, configuration fields, custom rules DSL, and discovery logic."
---

<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Configuration Reference

Zenzic reads a single `.zenzic.toml` file at the repository root. All fields are optional — Zenzic works out of the box with no configuration file at all.

!!! tip "Zero configuration"

    Most projects need no `.zenzic.toml` at all. Run `uvx zenzic check all` — if it passes,
    you're done. Only add configuration when you need to customise specific behaviour.

## Reference sections

This reference is split into focused pages:

| Page | Contents |
| :--- | :--- |
| [Configuration Reference](./configuration-reference.md) | `docs_dir`, exclusion lists, thresholds, scoring, `build_context`, adapter auto-detection |
| [Custom Rules DSL](../how-to/add-custom-rules.md) | `[[custom_rules]]` — project-specific regex lint rules in pure TOML |
| [Brand System](./brand-system.md) | Palette contract, semantic tokens, and HTML component styling rules |

---

## Full example

The simplest complete `.zenzic.toml` that exercises every section:

```toml
docs_dir = "docs"
excluded_dirs  = ["includes", "assets", "stylesheets", "overrides"]
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
