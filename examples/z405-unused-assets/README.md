<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Z405 UNREFERENCED_ASSET — Gallery Example

**Category:** Z4xx Structure
**Expected exit:** 1 (errors)

## What this demonstrates

`assets/banner.png` exists on disk but no document references it via a
Markdown image tag (`![alt](../assets/banner.png)`) or any other link.
Zenzic's asset scanner flags it as dead weight — undiscoverable by readers.

## Run it

```bash
zenzic lab z405
# or directly:
zenzic check assets
```bash

## Expected output

```bash
assets/banner.png  Z405  UNREFERENCED_ASSET  file exists but is never linked
```bash

## Real-world fix

Either reference the asset in a document, or delete it. Orphan assets
bloat the site and confuse readers navigating the file tree.
