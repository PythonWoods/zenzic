<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# custom-dir-target — Audit a Custom Directory

This example demonstrates running Zenzic against a directory that differs
from the `docs_dir` configured in `zenzic.toml`.

## What it demonstrates

- `zenzic check all content/` targets a custom content directory
- Zenzic patches `docs_dir` at runtime — `zenzic.toml` is unchanged
- The banner shows `./content/` to confirm the active target
- All Markdown files inside `content/` are fully audited
- The configured `docs/` tree is not scanned

## Run it

```bash
cd examples/custom-dir-target
zenzic check all content/
```

Expected exit code: **0** — banner shows `./content/ • N files (N docs, 0 assets)`.

## Why this is useful

- Audit a Hugo, Docusaurus, or Astro `content/` directory without reconfiguring
- Switch targets on the fly: `zenzic check all docs/`, `zenzic check all pages/`
- Run Zenzic as a linter in a monorepo where each sub-project has its own content

## Structure

```text
content/
  index.md           ← homepage content, audited by the demo
  guides/
    setup.md         ← setup guide, audited by the demo
docs/                ← configured docs_dir, NOT audited by the demo
zenzic.toml          ← docs_dir = "docs", overridden at runtime by CLI target
```
