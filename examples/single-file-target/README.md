<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# single-file-target — Audit a Single File

This example demonstrates scoping a Zenzic audit to **one specific file**
instead of the entire docs tree.

## What it demonstrates

- `zenzic check all README.md` targets a single Markdown file
- Zenzic auto-selects the `StandaloneAdapter` when the file lives outside `docs_dir`
- The banner reports `1 file (1 docs, 0 assets)` — not the full site count
- Only findings for the requested file appear in the report
- The `docs/` directory is untouched: its files are not scanned

## Run it

```bash
cd examples/single-file-target
zenzic check all README.md
```

Expected exit code: **0** — banner shows `./README.md • 1 file (1 docs, 0 assets)`.

## Why this is useful

- Quickly lint a project README before committing, without running a full scan
- Audit a changelog, release note, or any one-off Markdown file
- Integrate into a pre-commit hook that only checks staged files

## Structure

```text
README.md        ← this file — the single-file target in the demo
docs/
  index.md       ← part of the configured docs tree, not audited by the demo
zenzic.toml      ← docs_dir = "docs", engine = "standalone"
```
