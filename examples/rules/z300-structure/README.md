<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Reference Graph Integrity

Exercises Z301 (`DANGLING_REF`), Z302 (`DEAD_DEF`), and Z303 (`DUPLICATE_DEF`).

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| DANGLING_REF | Z301 | `[ref][missing-id]` — link target `missing-id` not defined |
| DEAD_DEF | Z302 | `[unused-def]: https://example.com` — definition never referenced |
| DUPLICATE_DEF | Z303 | `[anchor]: …` defined twice in the same file |

## Expected exits

```text
zenzic check references  # EXIT 1 — Z301 ×1, Z302 ×1, Z303 ×1
zenzic check all         # EXIT 1
```

## Files

- [`index.md`](docs/index.md) — Contains all three reference-graph violations
