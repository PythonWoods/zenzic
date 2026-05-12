<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Security Lab — Fenced Block Credential Scanner Test

This file verifies that the credential scanner scans **every line of source**, including
lines inside fenced code blocks. It exists to prevent a regression where
credentials inside `bash` or unlabelled examples could silently bypass detection.

Run from this directory:

```bash
zenzic check references   # triggers credential detection (exit 2)
```

---

## Layer 3 — Credentials Inside Fenced Blocks

The credential scanner must fire on these blocks even though no build engine would ever
render a credential hidden inside a code example as a live secret.

### Unlabelled fence

```text
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLEKEY
```

### Bash fence

```bash
export STRIPE_SECRET=sk_live_XXXXXXXXXXXXXXXXXXXXXXXX
```

Expected credential scanner output:

```text
[CREDENTIAL] fenced.md:20 — aws-access-key detected in line
[CREDENTIAL] fenced.md:26 — stripe-live-key detected in line
```

Exit code: **2**

---

## Why code blocks are not a safe hiding place

A credential committed inside a bash example is still a committed credential.
It lives in git history, is indexed by code-search tools, and may be extracted
by automated scanners that do not respect Markdown formatting.

The credential scanner deliberately ignores the fence boundary: **no line is invisible.**
