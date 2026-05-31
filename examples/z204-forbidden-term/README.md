<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z204 FORBIDDEN_TERM — Gallery Example

**Category:** Z2xx Security (Privacy Gate)
**Expected exit:** 2 (non-suppressible — policy violation)

## What this demonstrates

`.zenzic.local.toml` declares `ProjectX` as a forbidden term (internal codename).
`docs/index.md` mentions `ProjectX` in its content — triggering Z204 FORBIDDEN_TERM.

The CLI displays:

```text
✘ POLICY VIOLATION DETECTED
```

This banner distinguishes Z204 (governance enforcement) from Z201 (`SECURITY BREACH DETECTED`
for credential leaks), even though both share Exit code 2 and are non-suppressible.

## Run it

```bash
zenzic lab z204
# or directly:
zenzic check all
```

## Expected output

```text
✘ POLICY VIOLATION DETECTED

docs/index.md:9:  Z204  FORBIDDEN_TERM  Forbidden term detected — remove from documentation: 'ProjectX'
```

Exit code **2**.

## Local Sanctuary — .zenzic.local.toml

In real projects, `.zenzic.local.toml` is **git-ignored** so the list of confidential
terms stays off the public repository. The gate still enforces at every scan.

```toml
# .zenzic.local.toml (git-ignored)
[core]
forbidden_patterns = [
    "ProjectX",
    "staging.internal.corp",
]
```

## Fix

Remove or replace the forbidden term in the documentation source.
To update the allowed list, edit `.zenzic.local.toml` (never `.zenzic.toml`).
