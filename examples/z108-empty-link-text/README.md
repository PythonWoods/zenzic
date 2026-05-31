<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z108 EMPTY_LINK_TEXT — Gallery Example

**Category:** Z1xx Link Integrity
**Expected exit:** 1 (errors)

## What this demonstrates

`docs/index.md` contains `[](guide.md)` — a link whose label is empty.
Empty link text is inaccessible to screen readers (WCAG 2.1 §2.4.4 — Link Purpose)
and renders as an invisible clickable element.

## Run it

```bash
zenzic lab z108
# or directly:
zenzic check links
```

## Expected output

```text
docs/index.md:7:  Z108  EMPTY_LINK_TEXT  link to 'guide.md' has no label
```

Exit code **1**.

## Fix

Add a descriptive link label: `[Guide](guide.md)`.
