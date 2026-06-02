<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z404 CONFIG_ASSET_MISSING — Gallery Example

**Category:** Z4xx Topology & Assets
**Expected exit:** 0 (warning)

## What this demonstrates

`mkdocs.yml` declares `theme.logo: assets/logo.svg` but `docs/assets/logo.svg`
does not exist on disk. Zenzic fires Z404 CONFIG_ASSET_MISSING.

## Run it

```bash
cd examples/z404-config-asset-missing
uvx zenzic check all
```

## Expected output

```text
docs/docs/assets/logo.svg  !  [Z404]  logo asset not found on disk:
'docs/assets/logo.svg' (declared as theme.logo: 'assets/logo.svg' in mkdocs.yml)
```
