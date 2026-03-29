<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Path Traversal — Shield Layer 1

This file demonstrates a focused path traversal attack. Zenzic Shield classifies
the link below as `PathTraversal` — not `FileNotFound` — and blocks it before any
filesystem access occurs.

```bash
zenzic check links --strict   # triggers PathTraversal, exit 1
```

## Attack vector

[Read /etc/passwd](../../etc/passwd)

Expected output:

```text
[ERROR] security_lab/traversal.md — PathTraversal: ../../etc/passwd escapes docs root
```

The distinction matters: a `FileNotFound` error might suggest the file simply needs to be
created. A `PathTraversal` error is unambiguous — this is a hostile or misconfigured link
that must never reach the filesystem.

See also: [absolute.md](absolute.md) for the Portability Enforcement Layer demo.
