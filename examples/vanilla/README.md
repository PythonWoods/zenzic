<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# vanilla — Engine-Agnostic Docs Quality Gate

This example demonstrates Zenzic running in **Vanilla mode**: no MkDocs, no
Zensical, no build engine of any kind. Just Markdown files and a `zenzic.toml`.

## What it demonstrates

- `engine = "vanilla"` enables engine-agnostic mode
- Links, snippets, placeholders, assets, and custom rules are all checked
- The orphan check is skipped — with no declared nav, every file is reachable
- `fail_under = 80` enforces a minimum quality score
- A `[[custom_rules]]` rule (`ZZ-NOHTML`) warns against raw HTML in Markdown

## Run it

```bash
cd examples/vanilla
zenzic check all
```

Expected exit code: **0** — `SUCCESS: All checks passed.`

## Who this is for

Any team writing Markdown documentation without MkDocs or Zensical:

- Hugo, Docusaurus, Sphinx, Astro, Jekyll
- GitHub wikis or plain Markdown repos
- Projects that have not yet chosen a build engine

Zenzic checks the **source** — the build engine is irrelevant.

## Structure

```text
docs/
  index.md          ← home page
  guides/
    setup.md        ← install and configure
    api.md          ← programmatic interface reference
```
