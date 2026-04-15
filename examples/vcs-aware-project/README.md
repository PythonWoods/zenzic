<!--
SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev>
SPDX-License-Identifier: Apache-2.0
-->

# VCS-Aware Project Example

This example demonstrates Zenzic's **VCS-aware exclusion** features introduced
in v0.6.1rc1 "Obsidian Bastion".

## What this example shows

1. **`respect_vcs_ignore = true`** — Zenzic reads `.gitignore` and excludes
   matching files/directories from scans.
2. **`included_dirs`** — Force-includes `generated-api/` even though it is
   listed in `.gitignore`.
3. **`excluded_dirs`** — Excludes `drafts/` via config (L3).
4. **`excluded_file_patterns`** — Skips `CHANGELOG*.md` files.

## Running the example

```bash
cd examples/vcs-aware-project
zenzic check all
```

## Expected behaviour

- `docs/index.md` — scanned (normal file)
- `docs/guide.md` — scanned (normal file)
- `docs/generated-api/endpoints.md` — scanned (force-included despite .gitignore)
- `docs/drafts/wip.md` — excluded (L3 config: `excluded_dirs`)
- `site/`, `build/`, `dist/` — excluded (L2-VCS: .gitignore patterns)
