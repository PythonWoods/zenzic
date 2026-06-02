<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z102 — Anchor Missing Gallery Example

This page links to a section of `guide.md` that does not exist,
demonstrating **Z102 ANCHOR_MISSING** detection.

## Broken Anchor Reference

- [Nonexistent Section](guide.md#nonexistent-section) — the fragment `#nonexistent-section` is not defined in `guide.md` → **Z102**

## What Zenzic Reports

```text
docs/index.md:11:  Z102  ANCHOR_MISSING  guide.md#nonexistent-section — anchor not found on target page
```

Run `zenzic check links` to reproduce the finding.
