<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z202 PATH_TRAVERSAL — Gallery Example

**Category:** Z2xx Security
**Expected exit:** 1 (errors — non-suppressible)

## What this demonstrates

`docs/index.md` contains `[Config](../../private/secret.txt)` — a link that
escapes the `docs/` directory boundary through `../..` traversal. The resolved
target lands outside `docs/` (at `examples/private/secret.txt`), which
Zenzic treats as a boundary violation regardless of whether the file exists.

This is **Z202 PATH_TRAVERSAL** (non-fatal). The fatal variant (**Z203**) fires
only when the traversal targets OS system directories (`/etc/`, `/root/`, `/proc/`).

Z202 is **non-suppressible** (cannot be silenced with inline `zenzic: ignore`)
and exits with code **1** (errors).

## Run it

```bash
zenzic lab z202
# or directly:
zenzic check links
```

## Expected output

```text
docs/index.md:7:  Z202  PATH_TRAVERSAL  '../../private/secret.txt' escapes the docs/ root boundary
```

Exit code **1**.

## Fix

Remove the traversal link. If the target is an internal resource, relocate it
under `docs/` and use a relative path.
