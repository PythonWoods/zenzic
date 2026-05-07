<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windows Path Integrity — Overview

This example demonstrates Z105 `ABSOLUTE_LINK` detection on Windows-style filesystem
paths encoded as absolute Markdown links.

**RED TEAM**: use `/C:/Windows/`, `/UNC/server/`, and `file:///` constructs as link
targets — techniques that work on a developer's local Windows machine but break entirely
when the documentation is deployed to any other host or path.

**BLUE TEAM**: Z105 `ABSOLUTE_LINK` fires on every link starting with `/` — the path
is environment-dependent and therefore a portability violation.

```bash
zenzic check links  # EXIT 1 — Z105 ABSOLUTE_LINK on every Windows-style path
zenzic check all    # EXIT 1
```

See [win-paths.md](win-paths.md) and [unc-paths.md](unc-paths.md).
