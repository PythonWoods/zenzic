<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Standalone Mode Example

This project has no build engine. There is no `mkdocs.yml`, no `zensical.toml`,
no Hugo config, no Docusaurus config. Just Markdown files and a `zenzic.toml`.

Zenzic runs in **Standalone Mode**: links, snippets, content quality, assets, and custom
rules are all checked. Orphan detection (Z402) is disabled — with no declared navigation
contract, there is no reference set to compare against.

## Run it

```bash
cd examples/standalone
zenzic check all
```

Expected result: `SUCCESS: All checks passed.`

## What this example demonstrates

- `engine = "standalone"` in `zenzic.toml` enables engine-agnostic mode
- `fail_under = 80` enforces a minimum quality score
- A `[[custom_rules]]` rule warns against raw HTML in Markdown
- Internal links between pages are validated without any build tool
- Python snippets are syntax-checked without executing them

## Explore the docs

- [Setup guide](guides/setup.md) — install and configure this project
- [Python API](guides/api.md) — programmatic interface reference

## Who should use Standalone Mode

Any team that writes Markdown documentation but does not use MkDocs or Zensical:
Hugo, Docusaurus, Sphinx, Astro, Jekyll, plain GitHub wikis, or no build tool at all.
Zenzic checks the source — the build engine is irrelevant.
