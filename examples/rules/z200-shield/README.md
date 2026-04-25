<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Shield Extreme

Drives the Shield credential scanner to its limits through three advanced obfuscation
techniques: Base64 encoding, percent-encoding, and mixed-case prefix randomisation.

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| CREDENTIAL | Z201 | Credential-shaped patterns after normalisation |

## Expected exits

```text
zenzic check references  # EXIT 2 — Z201 SHIELD on every file
zenzic check all         # EXIT 2
```

## Files

- [`base64-secrets.md`](docs/base64-secrets.md) — Base64-encoded credential strings
- [`encoded-creds.md`](docs/encoded-creds.md) — Percent-encoded credential patterns
- [`mixed-case.md`](docs/mixed-case.md) — Mixed-case obfuscation of credential prefixes
