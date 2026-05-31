<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z105 — Absolute Path Gallery Example

This page uses an absolute path link, demonstrating **Z105 ABSOLUTE_PATH** detection.

## Absolute Path Link

- [Guide](/guide) — uses `/guide` (absolute) instead of `guide.md` (relative) → **Z105**

## What Zenzic Reports

```text
docs/index.md:7:  Z105  ABSOLUTE_PATH  '/guide' — use a relative path
```

Absolute paths break portability when a site is served from a subdirectory.
Run `zenzic check links` to reproduce the finding.
