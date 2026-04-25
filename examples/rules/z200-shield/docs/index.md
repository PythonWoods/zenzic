<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Link Graph Stress — Shield Extreme — Overview

This example drives the Shield credential scanner to its limits through three advanced
obfuscation techniques that naive scanners fail to normalise before pattern matching.

```bash
zenzic check references  # EXIT 2 — Z201 SHIELD on every file
zenzic check all         # EXIT 2
```

## Files

- [base64-secrets.md](base64-secrets.md) — Base64-encoded credential strings
- [encoded-creds.md](encoded-creds.md) — Percent-encoded credential patterns
- [mixed-case.md](mixed-case.md) — Mixed-case obfuscation of known credential prefixes
