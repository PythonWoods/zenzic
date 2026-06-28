<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z121 MISSING_OR_EMPTY_HREF — Gallery Example

**Category:** Z12x HTML Integrity
**Expected exit:** 1 (error)

`docs/index.md` contains `<a>` tags without an `href` attribute,
and `<img>` without `src`. The PolyglotExtractor emits **Z121** (error).

```bash
zenzic lab z121
```
