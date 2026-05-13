<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# I18N Parity

Exercises Z602 (`I18N_PARITY`).

## What fires

| Rule | Code | Trigger |
|:-----|:----:|:--------|
| I18N_PARITY | Z602 | Section present in default locale (EN) missing from non-default locale (IT) |

## Expected exits

```text
zenzic check i18n  # EXIT 1 — Z602 ×1
zenzic check all   # EXIT 1
```

## Files

- [`docs/en/index.md`](docs/en/index.md) — Full EN document (4 sections)
- [`docs/it/index.md`](docs/it/index.md) — IT translation missing the "Advanced Configuration" section → Z602

## Structure

```text
z602-i18n-parity/
├── zenzic.toml
└── docs/
    ├── en/
    │   └── index.md   # default locale — 4 sections
    └── it/
        └── index.md   # non-default locale — 3 sections (missing 1 → Z602)
```
