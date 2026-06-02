<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z406 NAV_CONTRACT — Gallery Example

**Category:** Z4xx Topology & Assets
**Expected exit:** 1 (error)

## What this demonstrates

`mkdocs.yml` declares `extra.alternate` with `link: /it/` but no Italian
documentation pages exist — `/it/` is not in the Virtual Site Map.
Zenzic fires Z406 NAV_CONTRACT — a hard error mandating exit 1.

## Run it

```bash
cd examples/z406-nav-contract
uvx zenzic check all
```

## Expected output

```text
docs/(nav)  x  [Z406]  mkdocs.yml extra.alternate[it]: link '/it/' does not
correspond to any URL the build engine will generate. The Virtual Site Map
contains no entry for '/it/'.
```
