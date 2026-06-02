<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z107 CIRCULAR_ANCHOR — Gallery Example

**Category:** Z1xx Link Integrity
**Expected exit:** 0 (warning)

## What this demonstrates

`docs/guide.md` contains the link `[Setup](#setup)` inside the `## Setup`
section. The link text "Setup" slugifies to `#setup`, which is the same
fragment as the containing heading — a circular self-reference.

## Run it

```bash
cd examples/z107-circular-anchor
uvx zenzic check all
```

## Expected output

```text
docs/guide.md:13:51  !  [Z107]  Self-referential anchor link: '[Setup](#setup)'
slugifies to its own fragment. Replace with a meaningful target or remove the link.
```
