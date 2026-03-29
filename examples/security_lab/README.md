<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# security_lab — Zenzic Shield Test Fixture

This example intentionally triggers the Zenzic Shield (credential detection) and
the link checker (path traversal, absolute links). It is a pre-release regression
fixture for the Shield subsystem.

## What it demonstrates

| File | Trigger |
| --- | --- |
| `traversal.md` | Path traversal: `../../etc/passwd` escapes `docs/` |
| `attack.md` | Path traversal + three fake credential patterns (OpenAI, GitHub, AWS) |
| `absolute.md` | Absolute links (`/assets/logo.png`, `/etc/passwd`) |

## Run it

```bash
cd examples/security_lab

# Link check only — exits 1 (path traversal in traversal.md + attack.md)
zenzic check links --strict

# Reference check — exits 2 (Shield: fake credentials in attack.md)
zenzic check references

# Full suite — exits 2 (Shield takes priority over other failures)
zenzic check all
```

> **Note:** Exit code `2` (Shield event) cannot be suppressed by `--exit-zero`.
> This is by design — credential exposure is a hard build blocker.

## Credentials

The credentials in `attack.md` are **entirely fake** — they match the regex shape
of real credentials but are not valid tokens for any service. They exist solely to
exercise the Shield scanner. Do not replace them with real credentials.

## Engine

Uses `engine = "mkdocs"`. No i18n configuration.
