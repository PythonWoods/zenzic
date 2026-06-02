<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z302 DEAD_DEF — Gallery Example

**Category:** Z3xx Reference Integrity
**Expected exit:** 1 (warnings)

## What this demonstrates

`docs/index.md` defines `[setup]: https://example.com/setup` at the bottom
of the file, but the reference ID `setup` is never used by any `[text][setup]`
or `[setup]` link in the document.

Zenzic's reference scanner detects the orphan definition in Pass 3 (Integrity
Report) and reports it as Z302 DEAD_DEF — documentation debt hidden in the source.

## Run it

```bash
zenzic lab z302
# or directly:
zenzic check references
```

## Expected output

```text
docs/index.md:16:  Z302  DEAD_DEF  reference ID 'setup' defined but never used
```

Exit code **1**.

## Fix

Either delete the unused definition, or add a link that uses it:
`[Setup guide][setup]`.
