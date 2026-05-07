<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Unix Security Probe — Overview

This example demonstrates the two-layer Zenzic Shield against Unix-style attack vectors.

**RED TEAM** creates three attack scenarios:

- [Deep Traversal](deep-traversal.md) — multi-hop `../` chains targeting `/etc/passwd`,
  `/root/.ssh/`, `/etc/shadow` + credential reference definitions
- [Obfuscated](obfuscated.md) — credentials hidden in tables, blockquotes, link titles,
  and URL query parameters
- [Fenced](fenced.md) — credentials inside `bash`, `yaml`, and unlabelled code blocks

**BLUE TEAM** result: `zenzic check all` exits **2** (Shield credential detection).
Path traversal links additionally trigger `EXIT 1` via `check links`.

```bash
zenzic check links       # EXIT 1 — PATH_TRAVERSAL in deep-traversal.md
zenzic check references  # EXIT 2 — SHIELD credentials in all three files
zenzic check all         # EXIT 2 — Shield takes priority
```
