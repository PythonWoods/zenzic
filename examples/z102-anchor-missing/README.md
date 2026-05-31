<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z102 ANCHOR_MISSING — Gallery Example

**Category:** Z1xx Link Integrity
**Expected exit:** 1 (errors)

## What this demonstrates

`docs/index.md` contains a link to `guide.md#nonexistent-section`.
The target file `guide.md` exists on disk, but it defines no `#nonexistent-section`
anchor. Zenzic's link validator detects the dead fragment at analysis time — purely
filesystem-based, no HTTP request needed.

## Run it

```bash
zenzic lab z102
# or directly:
zenzic check links
```

## Expected output

```text
docs/index.md:7:  Z102  ANCHOR_MISSING  guide.md#nonexistent-section — anchor not found on target page
```

Exit code **1**.

## Fix

Add the heading `## Nonexistent Section` to `guide.md`, or update the link to a
heading that already exists (e.g. `guide.md#overview`).
