<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z101 — Link Integrity Gallery Example

This page intentionally references two files that do not exist,
demonstrating **Z101 LINK_BROKEN** detection.

## Broken References

- [Getting Started](missing.md) — this file does not exist → **Z101**
- [Setup Guide](guide/setup.md) — this directory does not exist → **Z101**

## What Zenzic Reports

```text
docs/index.md:7:  Z101  LINK_BROKEN  [missing.md] target not found on disk
docs/index.md:8:  Z101  LINK_BROKEN  [guide/setup.md] target not found on disk
```

Run `zenzic check links` to reproduce the findings.
