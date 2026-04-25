<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# SEO Coverage

Generates mass Z401 (`MISSING_DIRECTORY_INDEX`) and Z402 (`ORPHAN_PAGE`) findings
using a realistic docs structure with intentional coverage gaps.

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| MISSING_DIRECTORY_INDEX | Z401 | Directory with content but no `index.md` |
| ORPHAN_PAGE | Z402 | Page with no inbound links |

## Expected exits

```text
zenzic check seo  # EXIT 1 — Z401 ×3 (section-a/b/c), Z402 ×1 (orphan.md)
zenzic check all  # EXIT 1
```

## Files

- [`index.md`](docs/index.md) — Root index (baseline — PASS)
- [`section-a/page.md`](docs/section-a/page.md) — No `index.md` in dir → Z401
- [`section-b/page.md`](docs/section-b/page.md) — No `index.md` in dir → Z401
- [`section-c/page.md`](docs/section-c/page.md) — No `index.md` in dir → Z401
- [`orphan.md`](docs/orphan.md) — No inbound links → Z402
