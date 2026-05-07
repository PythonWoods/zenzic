<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Link Graph Stress

Exercises Z101 (`BROKEN_LINK`), Z102 (`BROKEN_ANCHOR`), and Z104 (`FILE_NOT_FOUND`)
under adversarial link graph conditions: circular cross-references, broken section
anchors, and links to non-existent files.

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| BROKEN_ANCHOR | Z102 | `#anchor` to a heading that does not exist |
| FILE_NOT_FOUND | Z104 | Link to a `.md` file that does not exist on disk |

## Expected exits

```text
zenzic check links  # EXIT 1 — Z102 ×13, Z104 ×2
zenzic check all    # EXIT 1
```

## Files

- [`index.md`](docs/index.md) — Root page linking to all nodes
- [`a.md`](docs/a.md) — Links to `b.md#nonexistent-configuration-section` (Z102)
- [`b.md`](docs/b.md) — Links back to `a.md#installation-guide` (Z102, circular)
- [`c.md`](docs/c.md) — Links to `missing-file.md` and `nonexistent-guide.md` (Z104)
- [`broken-anchors.md`](docs/broken-anchors.md) — Eleven broken `#anchor` references
