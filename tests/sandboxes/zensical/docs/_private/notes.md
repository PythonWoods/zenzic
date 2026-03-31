<!-- SPDX-FileCopyrightText: 2026 PythonWoods <dev@pythonwoods.dev> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Private Notes

TRAP: This file is inside a `_private/` directory.

Zensical ignores `_private/` directories during build.
ZensicalAdapter.classify_route() returns IGNORED for these paths.

Linking to this page from a non-private page is an error —
Zenzic rc4 emits UNREACHABLE_LINK (page is IGNORED, not just orphaned).
