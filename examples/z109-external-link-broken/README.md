<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z109 EXTERNAL_LINK_BROKEN — Gallery Example

**Category:** Z1xx Link Integrity
**Expected exit:** 1 (errors)

## What this demonstrates

`docs/index.md` contains a link to an external URL that cannot be reached or returns an HTTP error:
`[Broken Link](https://this-domain-does-not-exist-at-all-xyz.com)`.

Zenzic's link validator flags this as `Z109 EXTERNAL_LINK_BROKEN`.

## Run it

```bash
zenzic check links
```

## Expected output

```text
docs/index.md:7:  Z109  EXTERNAL_LINK_BROKEN  external link 'https://this-domain-does-not-exist-at-all-xyz.com' is broken
```

Exit code **1**.

## Fix

Correct the external URL or remove the broken link.
