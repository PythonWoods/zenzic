<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z201 CREDENTIAL\_SECRET — Credential Leak Demo

This fixture demonstrates **Z201 `CREDENTIAL_SECRET`**: a plaintext AWS access
key committed inside a documentation file triggers the Zenzic credential scanner,
raises `CredentialViolation`, and produces **exit code 2** (SECURITY BREACH).

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| CREDENTIAL\_SECRET | Z201 | AWS access key pattern in `docs/index.md` |

## Expected exits

```text
zenzic check credentials  # EXIT 2 — Z201 ×1 (aws-access-key)
zenzic check all          # EXIT 2 — security tier overrides quality score
```

## How to run

```bash
cd examples/rules/z201-credential-leak
uv run zenzic check all
```

## Why exit 2 is non-suppressible

The credential scanner operates as IO middleware (`safe_read_line`). When a
credential pattern is detected, `CredentialViolation` is raised before the line
reaches any parser. Exit code 2 cannot be suppressed by `--exit-zero`,
`exit_zero = true`, or any inline suppression comment — it is a security-tier
finding that must always surface.

## Files

- [`docs/index.md`](docs/index.md) — Contains a synthetic AWS key (rotate immediately
  if you accidentally use a real value here)
