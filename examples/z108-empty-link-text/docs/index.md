<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z108 — Empty Link Text Gallery Example

This page contains a link with an empty label, demonstrating **Z108 EMPTY_LINK_TEXT** detection.

## Empty Link

- [](guide.md) — empty label (no visible text for screen readers) → **Z108**

## What Zenzic Reports

```text
docs/index.md:10:  Z108  EMPTY_LINK_TEXT  link to 'guide.md' has no label
```

Run `zenzic check links` to reproduce the finding.
