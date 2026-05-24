<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z101 LINK_BROKEN — Gallery Example

**Category:** Z1xx Link Integrity
**Expected exit:** 1 (errors)

## What this demonstrates

`docs/index.md` contains two links that resolve to files not present on disk.
Zenzic's link checker (Z101) detects these at analysis time without making
any HTTP requests — the check is purely filesystem-based.

## Run it

```bash
zenzic lab z101
# or directly:
zenzic check links
```bash

## Expected output

```bash
docs/index.md  Z101  LINK_BROKEN  [missing.md] target not found on disk
docs/index.md  Z101  LINK_BROKEN  [guide/setup.md] target not found on disk
```bash
