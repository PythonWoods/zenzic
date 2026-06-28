<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z124 OPAQUE_HTML_CONTEXT — Gallery Example

**Category:** Z12x HTML Integrity
**Expected exit:** 1 (error)

Blacklisted attributes (event-handlers `on*`, shadow-routing `data-url` etc.)
make navigation opaque. Emits **Z124** (error).

```bash
zenzic lab z124
```
