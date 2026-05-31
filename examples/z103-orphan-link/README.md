<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z103 ORPHAN_LINK — Gallery Example

**Category:** Z1xx Link Integrity
**Expected exit:** 1 (warnings)
**Engine required:** zensical

## What this demonstrates

`docs/guide.md` exists on disk (no Z101 LINK_BROKEN), but it is **not listed**
in `zensical.toml`'s `nav`. Its status in the Virtual Site Map (VSM) is
`ORPHAN_BUT_EXISTING`. When `docs/index.md` links to it with `[Guide](guide.md)`,
Zenzic's `VSMBrokenLinkRule` emits Z103 ORPHAN_LINK — the link bypasses
the documented site navigation.

> **Note:** Z103 requires the **zensical engine**. The standalone engine has no
> navigation manifest, so `ORPHAN_BUT_EXISTING` is never assigned and Z103
> never fires.

## Run it

```bash
zenzic lab z103
# or directly:
zenzic check links
```

## Expected output

```text
docs/index.md:7:  Z103  ORPHAN_LINK  'guide.md' exists but is not reachable via site navigation
```

Exit code **1**.

## Fix

Either add `"guide.md"` to the `nav` array in `zensical.toml` to make it a
first-class navigation page, or remove the link if the page is not ready
for publication.
