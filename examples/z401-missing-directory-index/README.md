<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z401 MISSING_DIRECTORY_INDEX — Gallery Example

**Category:** Z4xx Topology & Assets
**Expected exit:** 0 (info)

## What this demonstrates

`docs/guide/` contains `page.md` but has no `index.md`.
Navigating to `/guide/` in the built site will return a 404.
Zenzic fires Z401 MISSING_DIRECTORY_INDEX as an info finding.

## Run it

```bash
cd examples/z401-missing-directory-index
uvx zenzic check all --show-info
```

## Expected output

```text
docs/guide  i  [Z401]  Directory contains Markdown files but has no index page
— the directory URL may return a 404.
```
