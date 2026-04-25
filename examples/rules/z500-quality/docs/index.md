<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Quality Gate — Overview

This example exercises Z501 (`PLACEHOLDER`) and Z503 (`SNIPPET_NOT_FOUND`) across five
documents: a full-length baseline and four deliberately broken files.

```bash
zenzic check quality  # EXIT 1 — Z501 ×3, Z503 ×1
zenzic check all      # EXIT 1
```

## Files

- [index.md](index.md) — Full-length reference document (baseline — PASS)
- [stub-alpha.md](stub-alpha.md) — Under 50 words → Z501 PLACEHOLDER
- [stub-beta.md](stub-beta.md) — Contains literal `TODO` marker → Z501 PLACEHOLDER
- [stub-gamma.md](stub-gamma.md) — `FIXME` marker + under 50 words → Z501 PLACEHOLDER
- [bad-snippet.md](bad-snippet.md) — `@include` to a nonexistent snippet → Z503
