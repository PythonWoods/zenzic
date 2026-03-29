<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Security Lab — Zenzic Shield Test

This file intentionally contains patterns that trigger both layers of the **Zenzic Shield**.
It exists to verify Shield behaviour before releases. Run from the repo root:

```bash
zenzic check links --strict          # triggers PathTraversal
zenzic check references              # triggers credential detection (Exit 2)
```

---

## Layer 1 — Path Traversal

The link below attempts to escape the `docs/` root. Zenzic Shield classifies it as
`PathTraversal` — not a generic `FileNotFound` — and blocks it before any filesystem
access occurs.

[Exploit](../../../etc/passwd)

Expected output:

```text
[ERROR] security_lab/attack.md — PathTraversal: ../../../etc/passwd escapes docs root
```

---

## Layer 2 — Credential Detection

The reference definitions below embed intentionally fake, credential-shaped patterns.
They exist **solely to exercise the Shield scanner** during pre-release testing.
Do not substitute real credentials — the Shield will trigger Exit 2 immediately.

Expected output:

```text
╔══════════════════════════════════════╗
║        SECURITY CRITICAL             ║
║  Secret(s) detected in documentation ║
╚══════════════════════════════════════╝

  [SHIELD] examples/security_lab/attack.md:21 — openai-api-key detected in URL
  [SHIELD] examples/security_lab/attack.md:22 — github-token detected in URL
  [SHIELD] examples/security_lab/attack.md:23 — aws-access-key detected in URL

Build aborted. Rotate the exposed credential immediately.
```

Exit code: **2**
