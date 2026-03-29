<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Absolute Link Violation — Portability Enforcement Layer

This file demonstrates the **Absolute Link Prohibition** introduced in `0.3.0-rc2`.
Links starting with `/` are rejected before the resolver is consulted.

```bash
zenzic check links --strict   # triggers AbsoluteLinkError, exit 1
```

## Why absolute paths are forbidden

An absolute path like `/assets/logo.png` is resolved relative to the **server root**,
not relative to the page. When the site is hosted at `example.com/docs/`, the browser
resolves `/assets/logo.png` as `example.com/assets/logo.png` — a 404.

Relative paths (`../assets/logo.png`) survive any hosting path change without modification.

## Attack / misconfiguration vector

[Logo (absolute — will break in subdirectory hosting)](/assets/logo.png)

[Root filesystem attempt (absolute)](/etc/passwd)

Expected output:

```text
[ERROR] security_lab/absolute.md:20: '/assets/logo.png' uses an absolute path —
use a relative path (e.g. '../' or './') instead; absolute paths break portability
when the site is hosted in a subdirectory

[ERROR] security_lab/absolute.md:22: '/etc/passwd' uses an absolute path —
use a relative path (e.g. '../' or './') instead; absolute paths break portability
when the site is hosted in a subdirectory
```

Note: `/etc/passwd` is caught by the **Portability Enforcement Layer** (absolute path),
not by the Shield (path traversal). The Shield catches relative escapes (`../../`);
this layer catches environment-dependent absolute roots (`/`).

See also: [traversal.md](traversal.md) for the Shield path traversal demo.
