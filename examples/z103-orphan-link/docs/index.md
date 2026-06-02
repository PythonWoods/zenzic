<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z103 — Orphan Link Gallery Example

This page links to a page that exists on disk but is not in the site navigation,
demonstrating **Z103 ORPHAN_LINK** detection.

## Overview

Welcome to the Z103 demonstration. This page (`index.md`) is listed in the
`zensical.toml` nav and is reachable through the site menu.

The following link points to a page that exists on disk but has no nav entry:

- [Guide](guide.md) — `guide.md` exists on disk, but it is **not in the nav** → **Z103**

## What Zenzic Reports

```text
docs/index.md:16:  Z103  ORPHAN_LINK  'guide.md' exists but is not reachable via site navigation
```

Run `zenzic check links` to reproduce the finding.
