<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z601 BRAND_OBSOLESCENCE — Gallery Example

**Category:** Z6xx Governance
**Expected exit:** 1 (errors)

## What this demonstrates

`.zenzic.toml` declares `governance.brand_obsolescence = ["OldPlatform"]`.
`docs/index.md` mentions "OldPlatform" twice — Zenzic flags each occurrence
as **Z601 BRAND_OBSOLESCENCE**, signalling stale branding that confuses readers.

## Run it

```bash
zenzic lab z601
# or directly:
zenzic check all
```bash

## Expected output

```bash
docs/index.md  Z601  BRAND_OBSOLESCENCE  "OldPlatform" is a deprecated brand name
```bash

## Real-world fix

Replace the deprecated name, or suppress with an inline comment if the
reference is historically intentional:

```markdown
<!-- zenzic:ignore: Z601 intentional historical context -->
This project was migrated from **OldPlatform** in Q1 2026.
```bash
