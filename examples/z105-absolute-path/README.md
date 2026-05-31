<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z105 ABSOLUTE_PATH — Gallery Example

**Category:** Z1xx Link Integrity
**Expected exit:** 1 (errors)

## What this demonstrates

`docs/index.md` contains `[Guide](/guide)` — a link using an absolute path
starting with `/`. Absolute paths are non-portable: when a site is hosted in
a subdirectory (`https://example.com/my-docs/`), `/guide` resolves to the
server root instead of the docs root, producing a broken link at runtime.

## Run it

```bash
zenzic lab z105
# or directly:
zenzic check links
```

## Expected output

```text
docs/index.md:7:  Z105  ABSOLUTE_PATH  '/guide' — use a relative path (e.g. guide.md or ./guide.md)
```

Exit code **1**.

## Fix

Replace `/guide` with a relative path: `guide.md` or `./guide.md`.
