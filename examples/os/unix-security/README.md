<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Unix Security Probe

Demonstrates the two-layer Zenzic Shield against Unix-style attack vectors using a
Red/Blue team exercise across three escalating attack documents.

## Scenario

A malicious contributor attempts to embed path traversal chains and credential-shaped
patterns in documentation using every Markdown structural hiding technique available:
prose, tables, blockquotes, link titles, URL query parameters, and fenced code blocks.

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| PATH_TRAVERSAL | Z202 | `../` chains escaping the docs root |
| CREDENTIAL | Z201 | Credential-shaped patterns in any source line |

## Expected exits

```text
zenzic check links       # EXIT 1 — Z202 PATH_TRAVERSAL (deep-traversal.md)
zenzic check references  # EXIT 2 — Z201 SHIELD credentials (all three files)
zenzic check all         # EXIT 2 — Shield takes priority over link errors
```

## Files

- [`deep-traversal.md`](docs/deep-traversal.md) — Multi-hop `../` chains + credential ref defs
- [`obfuscated.md`](docs/obfuscated.md) — Credentials in tables, blockquotes, link titles, URL params
- [`fenced.md`](docs/fenced.md) — Credentials inside bash, yaml, and text fenced code blocks
