<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Quality Gate

Exercises Z501 (`PLACEHOLDER`) and Z503 (`SNIPPET_NOT_FOUND`) across five documents:
a full-length baseline and four deliberately broken files.

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| PLACEHOLDER | Z501 | Under 50 words, or contains `TODO`/`FIXME` |
| SNIPPET_NOT_FOUND | Z503 | `@include` targeting a nonexistent snippet |

## Expected exits

```text
zenzic check quality  # EXIT 1 — Z501 ×3, Z503 ×1
zenzic check all      # EXIT 1
```

## Files

- [`index.md`](docs/index.md) — Full-length reference document (baseline — PASS)
- [`stub-alpha.md`](docs/stub-alpha.md) — Under 50 words → Z501
- [`stub-beta.md`](docs/stub-beta.md) — `TODO` marker → Z501
- [`stub-gamma.md`](docs/stub-gamma.md) — `FIXME` marker + under 50 words → Z501
- [`bad-snippet.md`](docs/bad-snippet.md) — `@include` to nonexistent snippet → Z503
