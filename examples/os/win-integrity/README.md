<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windows Path Integrity

Demonstrates Z105 `ABSOLUTE_LINK` detection on Windows-style filesystem paths encoded
as absolute Markdown links.

## Scenario

Documentation authored on Windows may embed drive-letter paths (`/C:/...`), UNC network
share paths (`/UNC/server/share/`), or `file:///` URIs as link targets. These resolve
correctly on the author's machine but break on every other host or deployment target.

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| ABSOLUTE_LINK | Z105 | Any link target beginning with `/` |

## Expected exits

```text
zenzic check links  # EXIT 1 — Z105 ABSOLUTE_LINK (×16 links across two files)
zenzic check all    # EXIT 1
```

## Files

- [`win-paths.md`](docs/win-paths.md) — Drive-letter paths (`/C:/`, `/D:/`, `/Z:/`)
- [`unc-paths.md`](docs/unc-paths.md) — UNC shares (`/UNC/server/`) and `file:///`
