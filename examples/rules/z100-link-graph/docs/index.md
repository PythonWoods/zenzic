<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Link Graph Stress — Overview

This example exercises Z101 (`BROKEN_LINK`), Z102 (`BROKEN_ANCHOR`), and Z104
(`FILE_NOT_FOUND`) under adversarial link graph conditions: circular cross-references,
broken section anchors, and links to non-existent files.

```bash
zenzic check links  # EXIT 1 — Z101/Z102/Z104 across multiple files
zenzic check all    # EXIT 1
```

## Structure

- [a.md](a.md) — links to a non-existent section in b.md (Z102)
- [b.md](b.md) — links back to a.md with a broken anchor (circular Z102)
- [c.md](c.md) — links to missing-file.md (Z104) and to non-existent file.md (Z101)
- [broken-anchors.md](broken-anchors.md) — ten+ broken `#anchor` references
