<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# SEO Coverage — Overview

This example generates mass Z401 (`MISSING_DIRECTORY_INDEX`) and Z402 (`ORPHAN_PAGE`)
findings by creating a realistic docs structure with intentional coverage gaps.

```bash
zenzic check seo  # EXIT 1 — Z401 ×3, Z402 ×1
zenzic check all  # EXIT 1
```

## Structure

- `section-a/` — has `page.md` but no `index.md` → Z401
- `section-b/` — has `page.md` but no `index.md` → Z401
- `section-c/` — has `page.md` but no `index.md` → Z401
- `orphan.md` — exists in docs root but has no inbound links → Z402

See also: [orphan.md](orphan.md)
