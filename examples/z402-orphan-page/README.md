<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z402 ORPHAN_PAGE — Gallery Example

**Category:** Z4xx Asset Quality
**Expected exit:** 1 (warnings)
**Engine required:** zensical

## What this demonstrates

`docs/secret.md` exists on disk but is **not listed** in `zensical.toml`'s
`nav`. Without a navigation entry, no visitor can reach it through the site
menu — it is an orphan page, reachable only by direct URL guess or search crawl.

`docs/index.md` and `docs/guide.md` are properly listed in `nav`, so they
do not trigger Z402.

> **Note:** Z402 requires the **zensical engine** (`engine = "zensical"` in
> `.zenzic.toml`). The standalone engine has no navigation manifest, so
> `find_orphans()` always returns an empty list.

## Run it

```bash
zenzic lab z402
# or directly:
zenzic check assets
```

## Expected output

```text
docs/secret.md:1:  Z402  ORPHAN_PAGE  'secret.md' is not reachable via site navigation
```

Exit code **1**.

## Fix

Either add `"secret.md"` to the `nav` array in `zensical.toml`,
or delete the file if it is no longer needed.
