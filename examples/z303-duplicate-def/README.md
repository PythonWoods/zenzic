<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z303 DUPLICATE_DEF — Gallery Example

**Category:** Z3xx Reference Integrity
**Expected exit:** 1 (warnings)

## What this demonstrates

`docs/index.md` defines the reference ID `api` twice — once pointing to the
v1 API URL and once to the v2 API URL. Markdown renderers silently pick one
definition (usually the last), creating silent link drift.

Zenzic's reference scanner detects this ambiguity in Pass 2 (Harvest) and
reports it as Z303 DUPLICATE_DEF.

## Run it

```bash
zenzic lab z303
# or directly:
zenzic check references
```

## Expected output

```text
docs/index.md:13:  Z303  DUPLICATE_DEF  reference ID 'api' defined more than once
```

Exit code **1**.

## Fix

Remove the duplicate. Use distinct IDs if both targets are needed:
`[api-v1]: https://api-v1.example.com` and `[api-v2]: https://api-v2.example.com`.
