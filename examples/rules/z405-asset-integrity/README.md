<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Asset Integrity

Exercises Z405 (`UNUSED_ASSET`) and Z406 (`NAV_CONTRACT`).

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| UNUSED_ASSET | Z405 | Image file present in `assets/` but not referenced by any document |
| NAV_CONTRACT | Z406 | Document present in `docs/` but not listed in the navigation contract |

## Expected exits

```text
zenzic check assets  # EXIT 1 — Z405 ×1
zenzic check nav     # EXIT 1 — Z406 ×1
zenzic check all     # EXIT 1
```

## Files

- [`docs/index.md`](docs/index.md) — Main document (in nav contract — PASS)
- [`docs/orphan.md`](docs/orphan.md) — Present in `docs/` but absent from nav contract → Z406
- [`assets/logo.png`](assets/logo.png) — Stub asset file not referenced by any document → Z405
