<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z104 FILE_NOT_FOUND — Gallery Example

**Category:** Z1xx Link Integrity
**Expected exit:** 1 (error)

## What this demonstrates

`docs/index.md` contains a link to `api/reference.md`, which does not exist on
disk. Zenzic fires Z104 FILE_NOT_FOUND — a hard error that mandates exit 1.

## Run it

```bash
cd examples/z104-file-not-found
uvx zenzic check all
```

## Expected output

```text
docs/index.md:10:44  x  [Z104]  'api/reference.md' not found in docs
```
