<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z403 MISSING_ALT — Gallery Example

**Category:** Z4xx Asset Quality
**Expected exit:** 1 (warnings)

## What this demonstrates

`docs/index.md` contains `![](diagram.png)` — an image element whose alt text
is empty. Images without alt text are inaccessible to screen readers and fail
WCAG 2.1 §1.1.1 (Non-text Content).

> **Note:** Zenzic does **not** perform I/O on image paths. Z403 fires on the
> `![](url)` syntax regardless of whether the image file exists on disk. This
> is intentionally different from Z101, which validates link targets.

## Run it

```bash
zenzic lab z403
# or directly:
zenzic check assets
```

## Expected output

```text
docs/index.md:7:  Z403  MISSING_ALT  image 'diagram.png' has no alt text
```

Exit code **1**.

## Fix

Add a descriptive alt text: `![Architecture diagram showing component layout](diagram.png)`.
For decorative images, use an explicit empty alt: `![](diagram.png){aria-hidden="true"}`
(syntax varies by renderer).
